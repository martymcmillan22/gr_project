import uuid
from django.http import HttpResponse
from django.utils import timezone

from django.core.cache import cache
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_middle_layer.models import ProjectNode
from project_middle_layer.exports import build_semantic_export_payload, export_payload_to_json
from project_middle_layer.models import SemanticPipeline, SemanticSchedule
from project_middle_layer.integrations import (
    get_active_integration_by_key,
    run_inbound_integration_sync,
    run_outbound_integration_sync,
)
from project_middle_layer.api_gateway import gateway_dispatch, gateway_health_status, gateway_route_map, gateway_schema_introspection
from project_middle_layer.analytics import build_semantic_analytics_dashboard
from project_middle_layer.audit import record_semantic_audit_log
from project_middle_layer.btif_plus import btif_plus_compatibility_matrix, decode_btif_plus, encode_btif_plus, validate_btif_plus
from project_middle_layer.collaboration import acquire_edit_session, heartbeat_edit_session, release_edit_session
from project_middle_layer.extensions import apply_semantic_extension, rollback_semantic_extension
from project_middle_layer.external_agents import register_external_agent, run_external_agent
from project_middle_layer.marketplace import build_marketplace_update_notifications, install_marketplace_item
from project_middle_layer.pipelines import run_semantic_pipeline
from project_middle_layer.permissions import has_semantic_capability
from project_middle_layer.plugins import load_plugin_registry
from project_middle_layer.schedules import run_semantic_schedule
from project_middle_layer.semantic_cross_sync import run_semantic_cross_sync
from project_middle_layer.semantic_merge import merge_semantic_states
from project_middle_layer.semantic_search import run_semantic_search
from project_middle_layer.lfo_engine import build_lfo_engine_envelope
from project_middle_layer.services import compile_and_store_project_node
from project_middle_layer.services import build_calculus_timeline_runtime_payload
from project_middle_layer.services import dispatch_calculus_timeline_runtime_events
from project_middle_layer.versioning import checkout_semantic_version, commit_semantic_version

from .serializers import (
    CollaborationSessionAcquireRequestSerializer,
    CollaborationSessionHeartbeatRequestSerializer,
    CollaborationSessionReleaseRequestSerializer,
    ProjectBatchCompileRequestSerializer,
    ProjectExportRequestSerializer,
    IntegrationInboundSyncRequestSerializer,
    IntegrationOutboundSyncRequestSerializer,
    ProjectNodeSerializer,
    ProjectNodeWriteSerializer,
    ProjectPipelineRunRequestSerializer,
    ProjectScheduleRunRequestSerializer,
    SemanticAnalyticsRequestSerializer,
    SemanticMergeRequestSerializer,
    SemanticSearchRequestSerializer,
    SemanticVersionCheckoutRequestSerializer,
    SemanticVersionCommitRequestSerializer,
    MarketplaceInstallRequestSerializer,
    ExtensionApplyRequestSerializer,
    GatewayDispatchRequestSerializer,
    BtifPlusExportRequestSerializer,
    BtifPlusValidateRequestSerializer,
    ExternalAgentRegisterRequestSerializer,
    ExternalAgentRunRequestSerializer,
    CrossSyncRequestSerializer,
    ProjectWizardStartSerializer,
    ProjectWizardTagsSerializer,
    CalculusTimelineRuntimeRequestSerializer,
    LfoEngineRequestSerializer,
)


WIZARD_TTL_SECONDS = 60 * 30


def _require_api_capability(request, capability: str, *, project=None):
    if not has_semantic_capability(request.user, capability, project=project):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
    return None


def _audit_api(request, *, action: str, project=None, payload: dict[str, object] | None = None, source: str = "api"):
    record_semantic_audit_log(
        actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action,
        project=project,
        payload=payload or {},
        source=source,
    )


def _wizard_cache_key(user_id: int, wizard_id: str) -> str:
    return f"project_middle_layer:wizard:{user_id}:{wizard_id}"


class ProjectNodeViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectNode.objects.all().order_by("-updated_at")


class ProjectMiddleLayerCompileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "compile.semantic")
        if denied:
            return denied
        serializer = ProjectNodeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        compiled, node = compile_and_store_project_node(serializer.validated_data)
        _audit_api(
            request,
            action="compile.semantic",
            project=node,
            payload={"slug": node.slug, "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", "")},
        )

        return Response(compiled, status=status.HTTP_200_OK)


class ProjectMiddleLayerBatchCompileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "compile.semantic")
        if denied:
            return denied
        request_serializer = ProjectBatchCompileRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        items = request_serializer.validated_data["projects"]
        atomic_mode = bool(request_serializer.validated_data.get("atomic", False))

        results: list[dict[str, object]] = []
        drift_values: list[float] = []
        confidence_values: list[int] = []
        compiled_count = 0
        failed_count = 0

        def process_item(index: int, item: dict[str, object]) -> None:
            nonlocal compiled_count, failed_count

            item_serializer = ProjectNodeWriteSerializer(data=item)
            if not item_serializer.is_valid():
                failed_count += 1
                results.append(
                    {
                        "index": index,
                        "status": "failed",
                        "errors": item_serializer.errors,
                    }
                )
                if atomic_mode:
                    raise ValueError(f"Batch compile validation failed at index {index}.")
                return

            compiled_payload, node = compile_and_store_project_node(item_serializer.validated_data)
            compiled_count += 1

            drift_risk = compiled_payload.get("drift_forecast", {}).get("risk", {}).get("blended_semantic_drift_risk", 0.0)
            confidence_score = compiled_payload.get("confidence", {}).get("confidence_score", 0)
            try:
                drift_values.append(float(drift_risk))
            except (TypeError, ValueError):
                drift_values.append(0.0)
            try:
                confidence_values.append(int(confidence_score))
            except (TypeError, ValueError):
                confidence_values.append(0)

            results.append(
                {
                    "index": index,
                    "status": "compiled",
                    "slug": node.slug,
                    "payload": compiled_payload,
                }
            )

        if atomic_mode:
            try:
                with transaction.atomic():
                    for index, item in enumerate(items):
                        process_item(index, item)
            except ValueError:
                return Response(
                    {
                        "atomic": True,
                        "status": "rolled_back",
                        "results": results,
                        "summary": {
                            "requested": len(items),
                            "compiled": 0,
                            "failed": len(items),
                            "average_drift_risk": 0.0,
                            "average_confidence_score": 0.0,
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            for index, item in enumerate(items):
                process_item(index, item)

        average_drift = round(sum(drift_values) / len(drift_values), 4) if drift_values else 0.0
        average_confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0.0

        _audit_api(
            request,
            action="batch.compile.semantic",
            payload={"requested": len(items), "compiled": compiled_count, "failed": failed_count},
        )

        return Response(
            {
                "atomic": atomic_mode,
                "status": "completed",
                "results": results,
                "summary": {
                    "requested": len(items),
                    "compiled": compiled_count,
                    "failed": failed_count,
                    "average_drift_risk": average_drift,
                    "average_confidence_score": average_confidence,
                },
            },
            status=status.HTTP_200_OK,
        )


class ProjectMiddleLayerCalculusTimelineAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        selected_slot = request.query_params.get("selected_slot", 1)
        try:
            normalized_selected_slot = int(selected_slot)
        except (TypeError, ValueError):
            normalized_selected_slot = 1

        payload = build_calculus_timeline_runtime_payload(selected_slot=normalized_selected_slot)
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CalculusTimelineRuntimeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = build_calculus_timeline_runtime_payload(**serializer.validated_data)
        dispatch_calculus_timeline_runtime_events(payload)
        return Response(payload, status=status.HTTP_200_OK)


class ProjectMiddleLayerLfoEngineAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = LfoEngineRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        timeline_snapshot = params.get("timeline_snapshot") if isinstance(params.get("timeline_snapshot"), dict) else {}
        synthesis_snapshot = params.get("synthesis_snapshot") if isinstance(params.get("synthesis_snapshot"), dict) else {}
        trigger_count = int(params.get("trigger_count") or 0)

        if not timeline_snapshot:
            runtime_payload = build_calculus_timeline_runtime_payload(
                selected_slot=int(params.get("selected_slot") or 1),
                completed_slots=params.get("completed_slots") or [],
            )
            selected_state = runtime_payload.get("selected_slot_state", {})
            selected_semantic = selected_state.get("state", {}) if isinstance(selected_state, dict) else {}
            completed_slots = runtime_payload.get("deterministic_progression", {}).get("completed_slots", [])
            timeline_snapshot = {
                "latest_slot_index": int(selected_state.get("slot_index") or 0),
                "latest_phase": str(selected_state.get("phase") or ""),
                "drift_score": float(selected_semantic.get("drift_score") or 0.0),
                "stability_score": float(selected_semantic.get("stability_score") or 0.0),
                "alignment_score": float(selected_semantic.get("alignment_score") or 0.0),
                "completion_ratio": round(len(completed_slots) / 16.0, 3),
            }
            if not synthesis_snapshot:
                risk_level = "low"
                drift_value = float(selected_semantic.get("drift_score") or 0.0)
                alignment_value = float(selected_semantic.get("alignment_score") or 0.0)
                if drift_value >= 0.67 or alignment_value <= 0.4:
                    risk_level = "medium"
                if drift_value >= 0.85 or alignment_value <= 0.2:
                    risk_level = "high"
                synthesis_snapshot = {
                    "risk_level": risk_level,
                    "drift_trend": "stable",
                    "alignment_trajectory": "stable",
                }

        payload = build_lfo_engine_envelope(
            timeline_snapshot=timeline_snapshot,
            synthesis_snapshot=synthesis_snapshot,
            trigger_count=trigger_count,
            feature_pathways=params.get("feature_pathways") or [],
        )
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LfoEngineRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        payload = build_lfo_engine_envelope(
            timeline_snapshot=params.get("timeline_snapshot") if isinstance(params.get("timeline_snapshot"), dict) else {},
            synthesis_snapshot=params.get("synthesis_snapshot") if isinstance(params.get("synthesis_snapshot"), dict) else {},
            trigger_count=int(params.get("trigger_count") or 0),
            feature_pathways=params.get("feature_pathways") or [],
        )
        return Response(payload, status=status.HTTP_200_OK)


class ProjectCreationWizardStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProjectWizardStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        wizard_id = uuid.uuid4().hex
        cache.set(
            _wizard_cache_key(request.user.id, wizard_id),
            {
                "wizard_id": wizard_id,
                "step": "start",
                "base": payload,
                "tags": None,
            },
            timeout=WIZARD_TTL_SECONDS,
        )

        return Response(
            {
                "wizard_id": wizard_id,
                "next_step": "tags",
                "expires_in_seconds": WIZARD_TTL_SECONDS,
            },
            status=status.HTTP_201_CREATED,
        )


class ProjectCreationWizardTagsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, wizard_id: str):
        serializer = ProjectWizardTagsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = _wizard_cache_key(request.user.id, wizard_id)
        draft = cache.get(key)
        if not draft:
            return Response({"detail": "Wizard session not found or expired."}, status=status.HTTP_404_NOT_FOUND)

        draft["tags"] = serializer.validated_data
        draft["step"] = "tags"
        cache.set(key, draft, timeout=WIZARD_TTL_SECONDS)

        return Response({"wizard_id": wizard_id, "next_step": "compile"}, status=status.HTTP_200_OK)


class ProjectCreationWizardCompileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, wizard_id: str):
        key = _wizard_cache_key(request.user.id, wizard_id)
        draft = cache.get(key)
        if not draft:
            return Response({"detail": "Wizard session not found or expired."}, status=status.HTTP_404_NOT_FOUND)

        if not draft.get("tags"):
            return Response({"detail": "Wizard tags step not completed."}, status=status.HTTP_400_BAD_REQUEST)

        base = draft["base"]
        tags = draft["tags"]

        compiled, _ = compile_and_store_project_node(
            {
                **base,
                **tags,
                "semantic_tags": tags["semantic_tags"],
                "metadata": {
                    **base.get("metadata", {}),
                    **tags.get("metadata", {}),
                },
            }
        )

        cache.delete(key)
        return Response(compiled, status=status.HTTP_200_OK)


class ProjectMiddleLayerExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_api_capability(request, "export.semantic")
        if denied:
            return denied
        serializer = ProjectExportRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        payload = build_semantic_export_payload(
            scope=params["scope"],
            project_slug=params.get("project_slug"),
            include_history=bool(params.get("include_history", False)),
            max_items=int(params.get("max_items", 100)),
            exported_by=getattr(request.user, "username", "api-user") or "api-user",
        )

        if params.get("download", False):
            stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
            scope_name = params["scope"] if params["scope"] == "all" else (params.get("project_slug") or "project")
            filename = f"project-middle-layer-semantic-export-{scope_name}-{stamp}.json"
            body = export_payload_to_json(payload)
            response = HttpResponse(body, content_type="application/json")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            _audit_api(request, action="export.semantic", payload={"scope": params["scope"], "download": True})
            return response

        _audit_api(request, action="export.semantic", payload={"scope": params["scope"], "download": False})
        return Response(payload, status=status.HTTP_200_OK)


class ProjectMiddleLayerPipelineRunAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "run.pipeline")
        if denied:
            return denied
        serializer = ProjectPipelineRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pipeline_slug = serializer.validated_data["pipeline_slug"]
        try:
            pipeline = SemanticPipeline.objects.get(slug=pipeline_slug, is_active=True)
        except SemanticPipeline.DoesNotExist:
            return Response({"detail": "Active semantic pipeline not found."}, status=status.HTTP_404_NOT_FOUND)

        run = run_semantic_pipeline(
            pipeline,
            triggered_by=getattr(request.user, "username", "api-user") or "api-user",
        )
        _audit_api(request, action="pipeline.run", payload={"pipeline_slug": pipeline.slug, "status": run.status})
        return Response(
            {
                "pipeline": pipeline.slug,
                "run_id": run.id,
                "status": run.status,
                "error_message": run.error_message,
                "result": run.result,
            },
            status=status.HTTP_200_OK if run.status == "completed" else status.HTTP_400_BAD_REQUEST,
        )


class ProjectMiddleLayerScheduleRunAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "run.schedule")
        if denied:
            return denied
        serializer = ProjectScheduleRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schedule_slug = serializer.validated_data["schedule_slug"]
        try:
            schedule = SemanticSchedule.objects.get(slug=schedule_slug)
        except SemanticSchedule.DoesNotExist:
            return Response({"detail": "Semantic schedule not found."}, status=status.HTTP_404_NOT_FOUND)

        run = run_semantic_schedule(
            schedule,
            triggered_by=getattr(request.user, "username", "api-user") or "api-user",
        )
        _audit_api(request, action="schedule.run", payload={"schedule_slug": schedule.slug, "status": run.status})
        return Response(
            {
                "schedule": schedule.slug,
                "run_id": run.id,
                "status": run.status,
                "error_message": run.error_message,
                "result": run.result,
            },
            status=status.HTTP_200_OK if run.status == "completed" else status.HTTP_400_BAD_REQUEST,
        )


class IntegrationInboundSyncAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = IntegrationInboundSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        api_key = request.headers.get("X-Semantic-Integration-Key", "")
        integration = get_active_integration_by_key(api_key, direction="inbound")
        if not integration:
            return Response({"detail": "Active inbound integration not found for API key."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            result = run_inbound_integration_sync(
                integration=integration,
                payload=serializer.validated_data["payload"],
                triggered_by=f"integration:{integration.slug}",
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class IntegrationOutboundSyncAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = IntegrationOutboundSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        api_key = request.headers.get("X-Semantic-Integration-Key", "")
        integration = get_active_integration_by_key(api_key, direction="outbound")
        if not integration:
            return Response({"detail": "Active outbound integration not found for API key."}, status=status.HTTP_401_UNAUTHORIZED)

        params = serializer.validated_data
        payload = run_outbound_integration_sync(
            integration=integration,
            scope=params["scope"],
            project_slug=params.get("project_slug"),
            include_history=bool(params.get("include_history", False)),
            max_items=int(params.get("max_items", 100)),
            triggered_by=f"integration:{integration.slug}",
        )
        return Response(payload, status=status.HTTP_200_OK)


class ProjectMiddleLayerSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_api_capability(request, "search.semantic")
        if denied:
            return denied
        serializer = SemanticSearchRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"]
        limit = int(serializer.validated_data.get("limit", 50))

        payload = run_semantic_search(query, limit=limit)
        _audit_api(request, action="search.semantic", payload={"query": query, "limit": limit})
        return Response(payload, status=status.HTTP_200_OK)


class ProjectMiddleLayerAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_api_capability(request, "analytics.semantic")
        if denied:
            return denied
        serializer = SemanticAnalyticsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        branch_filter = serializer.validated_data.get("branch_filter", "")
        tier_filter = serializer.validated_data.get("tier_filter", "")
        limit = int(serializer.validated_data.get("limit", 20))

        dashboard = build_semantic_analytics_dashboard(
            limit=limit,
            branch_filter=branch_filter,
            tier_filter=tier_filter,
        )
        latest = dashboard.get("latest")
        trend_points = dashboard.get("trend_points", [])

        payload = {
            "summary": {
                "snapshot_count": len(dashboard.get("snapshots", [])),
                "has_latest": latest is not None,
            },
            "filters": dashboard.get("filters", {}),
            "latest": {
                "id": latest.id,
                "created_at": latest.created_at,
                "project_count": latest.project_count,
                "drift_mean": latest.drift_mean,
                "drift_std": latest.drift_std,
                "confidence_mean": latest.confidence_mean,
                "confidence_std": latest.confidence_std,
                "stability_mean": latest.stability_mean,
                "stability_std": latest.stability_std,
                "branch_filter": latest.branch_filter,
                "tier_filter": latest.tier_filter,
                "chart_series": latest.chart_series,
            }
            if latest
            else None,
            "trend_points": trend_points,
            "facets": {
                "available_branches": dashboard.get("available_branches", []),
                "available_tiers": dashboard.get("available_tiers", []),
            },
        }
        _audit_api(request, action="analytics.semantic", payload={"branch_filter": branch_filter, "tier_filter": tier_filter, "limit": limit})
        return Response(payload, status=status.HTTP_200_OK)


class ProjectMiddleLayerVersionCommitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "version.commit")
        if denied:
            return denied
        serializer = SemanticVersionCommitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = ProjectNode.objects.filter(slug=serializer.validated_data["project_slug"]).first()
        if not project:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        version = commit_semantic_version(
            project=project,
            author=request.user,
            message=serializer.validated_data.get("message", ""),
        )
        _audit_api(request, action="version.commit", project=project, payload={"version_id": version.id, "version_number": version.version_number})
        return Response(
            {
                "version_id": version.id,
                "project_slug": project.slug,
                "version_number": version.version_number,
                "message": version.message,
            },
            status=status.HTTP_200_OK,
        )


class ProjectMiddleLayerVersionCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "version.checkout")
        if denied:
            return denied
        serializer = SemanticVersionCheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from project_middle_layer.models import SemanticVersion

        version = SemanticVersion.objects.select_related("project").filter(id=serializer.validated_data["version_id"]).first()
        if not version:
            return Response({"detail": "Version not found."}, status=status.HTTP_404_NOT_FOUND)
        project = checkout_semantic_version(version=version, actor=request.user)
        _audit_api(request, action="version.checkout", project=project, payload={"version_id": version.id, "version_number": version.version_number})
        return Response(
            {
                "project_slug": project.slug,
                "version_id": version.id,
                "version_number": version.version_number,
                "restored": True,
            },
            status=status.HTTP_200_OK,
        )


class ProjectMiddleLayerMergeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "merge.semantic")
        if denied:
            return denied
        serializer = SemanticMergeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = merge_semantic_states(
            serializer.validated_data["left"],
            serializer.validated_data["right"],
            base=serializer.validated_data.get("base", {}),
        )
        _audit_api(request, action="merge.semantic", payload={"has_conflicts": result.get("has_conflicts", False)})
        return Response(result, status=status.HTTP_200_OK)


class ProjectMiddleLayerCollaborationSessionAcquireAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "edit.semantic")
        if denied:
            return denied
        serializer = CollaborationSessionAcquireRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = ProjectNode.objects.filter(slug=serializer.validated_data["project_slug"]).first()
        if not project:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            session = acquire_edit_session(
                project=project,
                user=request.user,
                force_takeover=bool(serializer.validated_data.get("force_takeover", False)),
                lease_minutes=int(serializer.validated_data.get("lease_minutes", 20)),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        _audit_api(request, action="edit.session.acquire", project=project, payload={"session_id": session.id})
        return Response(
            {
                "session_id": session.id,
                "project_slug": project.slug,
                "status": session.status,
                "lease_expires_at": session.lease_expires_at,
            },
            status=status.HTTP_200_OK,
        )


class ProjectMiddleLayerCollaborationSessionHeartbeatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "edit.semantic")
        if denied:
            return denied
        serializer = CollaborationSessionHeartbeatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from project_middle_layer.models import SemanticEditSession

        session = SemanticEditSession.objects.select_related("project", "user").filter(id=serializer.validated_data["session_id"]).first()
        if not session:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.user_id != request.user.id:
            return Response({"detail": "Only the session owner can heartbeat this session."}, status=status.HTTP_403_FORBIDDEN)
        try:
            session = heartbeat_edit_session(
                session=session,
                user=request.user,
                lease_minutes=int(serializer.validated_data.get("lease_minutes", 20)),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_api(request, action="edit.session.heartbeat", project=session.project, payload={"session_id": session.id})
        return Response(
            {
                "session_id": session.id,
                "status": session.status,
                "lease_expires_at": session.lease_expires_at,
            },
            status=status.HTTP_200_OK,
        )


class ProjectMiddleLayerCollaborationSessionReleaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "edit.semantic")
        if denied:
            return denied
        serializer = CollaborationSessionReleaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from project_middle_layer.models import SemanticEditSession

        session = SemanticEditSession.objects.select_related("project", "user").filter(id=serializer.validated_data["session_id"]).first()
        if not session:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        if session.user_id != request.user.id:
            return Response({"detail": "Only the session owner can release this session."}, status=status.HTTP_403_FORBIDDEN)
        session = release_edit_session(session=session)
        _audit_api(request, action="edit.session.release", project=session.project, payload={"session_id": session.id})
        return Response(
            {
                "session_id": session.id,
                "status": session.status,
            },
            status=status.HTTP_200_OK,
        )


class MarketplaceListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_api_capability(request, "manage.marketplace")
        if denied:
            return denied
        from project_middle_layer.models import MarketplaceInstall, MarketplaceItem

        items = MarketplaceItem.objects.order_by("name")[:200]
        installs = MarketplaceInstall.objects.select_related("item", "owner")[:200]
        return Response(
            {
                "items": [
                    {
                        "slug": item.slug,
                        "name": item.name,
                        "item_type": item.item_type,
                        "current_version": item.current_version,
                        "is_active": item.is_active,
                    }
                    for item in items
                ],
                "installs": [
                    {
                        "item_slug": install.item.slug,
                        "installed_version": install.installed_version,
                        "status": install.status,
                        "owner": install.owner.username if install.owner else "",
                    }
                    for install in installs
                ],
                "update_notifications": build_marketplace_update_notifications(),
            },
            status=status.HTTP_200_OK,
        )


class MarketplaceInstallAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "manage.marketplace")
        if denied:
            return denied
        serializer = MarketplaceInstallRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = install_marketplace_item(
                item_slug=serializer.validated_data["item_slug"],
                requested_version=(serializer.validated_data.get("requested_version") or "").strip() or None,
                owner=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_api(request, action="marketplace.install", payload=result)
        return Response(result, status=status.HTTP_200_OK)


class ExtensionApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "manage.extensions")
        if denied:
            return denied
        serializer = ExtensionApplyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = apply_semantic_extension(extension_slug=serializer.validated_data["extension_slug"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_api(request, action="extension.apply", payload=result)
        return Response(result, status=status.HTTP_200_OK)


class ExtensionRollbackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "manage.extensions")
        if denied:
            return denied
        serializer = ExtensionApplyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = rollback_semantic_extension(extension_slug=serializer.validated_data["extension_slug"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_api(request, action="extension.rollback", payload=result)
        return Response(result, status=status.HTTP_200_OK)


class GatewayIntrospectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_api_capability(request, "gateway.inspect")
        if denied:
            return denied
        return Response(
            {
                "route_map": gateway_route_map(),
                "schema": gateway_schema_introspection(),
                "health": gateway_health_status(),
                "plugin_registry": load_plugin_registry(),
            },
            status=status.HTTP_200_OK,
        )


class GatewayDispatchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "gateway.dispatch")
        if denied:
            return denied
        serializer = GatewayDispatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = gateway_dispatch(
            route=serializer.validated_data["route"],
            requested_version=(serializer.validated_data.get("requested_version") or "").strip() or None,
        )
        _audit_api(request, action="gateway.dispatch", payload=payload)
        return Response(payload, status=status.HTTP_200_OK)


class BtifPlusExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "btif.interop")
        if denied:
            return denied
        serializer = BtifPlusExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = encode_btif_plus(project_slug=serializer.validated_data["project_slug"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        validation = validate_btif_plus(payload)
        result = {
            "payload": payload,
            "validation": validation,
            "compatibility": btif_plus_compatibility_matrix(),
        }
        _audit_api(request, action="btif.export", payload={"project_slug": serializer.validated_data["project_slug"], "valid": validation.get("valid", False)})
        return Response(result, status=status.HTTP_200_OK)


class BtifPlusValidateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "btif.interop")
        if denied:
            return denied
        serializer = BtifPlusValidateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = decode_btif_plus(serializer.validated_data["payload"])
        result = {
            "validation": validate_btif_plus(payload),
            "compatibility": btif_plus_compatibility_matrix(),
        }
        _audit_api(request, action="btif.validate", payload={"valid": result["validation"].get("valid", False)})
        return Response(result, status=status.HTTP_200_OK)


class ExternalAgentRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "manage.external_agents")
        if denied:
            return denied
        serializer = ExternalAgentRegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = register_external_agent(serializer.validated_data)
        payload = {"agent_slug": agent.slug, "status": agent.status}
        _audit_api(request, action="external.agent.register", payload=payload)
        return Response(payload, status=status.HTTP_200_OK)


class ExternalAgentRunAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "manage.external_agents")
        if denied:
            return denied
        serializer = ExternalAgentRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = run_external_agent(
                agent_slug=serializer.validated_data["agent_slug"],
                operation=serializer.validated_data["operation"],
                payload=serializer.validated_data.get("payload", {}),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_api(request, action="external.agent.run", payload={"agent_slug": result.get("agent_slug"), "status": result.get("status")})
        return Response(result, status=status.HTTP_200_OK)


class CrossSyncAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        denied = _require_api_capability(request, "sync.cross_platform")
        if denied:
            return denied
        serializer = CrossSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = run_semantic_cross_sync(
            sync_type=serializer.validated_data["sync_type"],
            target_platform=serializer.validated_data["target_platform"],
            project_slug=serializer.validated_data["project_slug"],
        )
        _audit_api(request, action="sync.cross_platform", payload=result)
        return Response(result, status=status.HTTP_200_OK)
