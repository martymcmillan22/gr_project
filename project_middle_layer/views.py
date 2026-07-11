import json

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views import View
from django.views.generic.edit import FormView
from urllib.parse import urlencode

from .api.serializers import ProjectNodeWriteSerializer
from .exports import build_semantic_export_payload, export_payload_to_json
from .forms import (
    BtifPlusForm,
    DistributedAgentRunForm,
    ExternalAgentForm,
    FederationPeerForm,
    MarketplaceInstallForm,
    ReplicationConfigForm,
    SemanticCrossSyncForm,
    SemanticCacheControlForm,
    SemanticExtensionForm,
    SemanticGatewayForm,
    SemanticPluginForm,
    SemanticShardForm,
    SemanticSyncForm,
    SemanticAuditFilterForm,
    SemanticChangeRequestForm,
    SemanticChangeReviewForm,
    SemanticEditSessionForm,
    SemanticPermissionForm,
    SemanticRoleForm,
    SemanticVersionCheckoutForm,
    SemanticVersionCommitForm,
    ProjectMiddleLayerAgentRunForm,
    ProjectMiddleLayerAnalyticsForm,
    ProjectMiddleLayerBatchCompileForm,
    ProjectMiddleLayerCompileForm,
    ProjectMiddleLayerExportForm,
    ProjectMiddleLayerSearchForm,
    ProjectMiddleLayerPipelineForm,
    ProjectMiddleLayerScheduleForm,
    ProjectMiddleLayerWebhookForm,
    ProjectMiddleLayerIntegrationForm,
)
from .models import (
    DistributedAgentRun,
    ExternalAgent,
    FederationPeer,
    MarketplaceInstall,
    MarketplaceItem,
    ProjectEvolutionSnapshot,
    ProjectNode,
    ReplicationConfig,
    SemanticCrossSyncLog,
    SemanticExtension,
    SemanticAlert,
    SemanticAnalyticsSnapshot,
    SemanticAgentRun,
    SemanticAuditLog,
    SemanticChangeRequest,
    SemanticEditSession,
    SemanticLineageRecord,
    SemanticPermission,
    SemanticPipeline,
    SemanticPipelineRun,
    SemanticRole,
    SemanticSchedule,
    SemanticScheduleRun,
    SemanticShard,
    SemanticSyncLog,
    SemanticVersion,
    SemanticWebhook,
    SemanticWebhookDelivery,
    SemanticIntegration,
    SemanticPlugin,
)
from .api_gateway import gateway_dispatch, gateway_health_status, gateway_route_map, gateway_schema_introspection
from .btif_plus import btif_plus_compatibility_matrix, decode_btif_plus, encode_btif_plus, validate_btif_plus
from .external_agents import register_external_agent, run_external_agent
from .extensions import apply_semantic_extension, rollback_semantic_extension
from .integrations import run_outbound_integration_sync
from .marketplace import build_marketplace_update_notifications, install_marketplace_item
from .analytics import build_semantic_analytics_dashboard, build_semantic_analytics_snapshot
from .agents import AGENT_NAMES, run_semantic_agent
from .insights import build_semantic_insights
from .pipelines import build_project_creation_payload, run_semantic_pipeline
from .schedules import run_semantic_schedule
from .semantic_search import run_semantic_search
from .webhooks import retry_webhook_delivery
from .semantic import build_semantic_diff
from .services import compile_and_store_project_node
from .audit import record_semantic_audit_log
from .collaboration import acquire_edit_session
from .permissions import has_semantic_capability, resolve_actor_by_username
from .review import apply_change_request, create_change_request
from .semantic_merge import merge_semantic_states
from .versioning import checkout_semantic_version, commit_semantic_version
from .distributed_agents import DISTRIBUTED_AGENT_NAMES, run_distributed_agent
from .federation import run_federated_insights, run_federated_lineage_cluster_mapping, run_federated_search
from .replication import run_replication
from .semantic_cache import flush_semantic_cache, get_or_set_cached, warm_semantic_cache
from .semantic_cross_sync import run_semantic_cross_sync
from .semantic_sync import run_semantic_sync
from .sharding import build_shard_map, rebalance_shards
from .plugins import load_plugin_registry, register_plugin, set_plugin_enabled


def _snapshot_to_diff_state(snapshot: ProjectEvolutionSnapshot) -> dict[str, object]:
    specialized_forms = snapshot.specialized_path.get("forms", []) if isinstance(snapshot.specialized_path, dict) else []
    final_identity_uri = ""
    if specialized_forms and isinstance(specialized_forms[0], dict):
        final_identity_uri = str(specialized_forms[0].get("final_identity_uri", ""))

    return {
        "label": f"Snapshot #{snapshot.id}",
        "identity_uri": snapshot.identity_uri,
        "semantic_tags": snapshot.semantic_tags,
        "drift_risk": snapshot.drift_risk,
        "branch_name": snapshot.branch_name,
        "confidence_score": snapshot.confidence_score,
        "stability_score": 0,
        "final_identity_uri": final_identity_uri,
    }


def _payload_to_diff_state(payload: dict[str, object], *, label: str) -> dict[str, object]:
    schema = payload.get("schema", {}) if isinstance(payload.get("schema", {}), dict) else {}
    identity = payload.get("identity_payload", {}).get("identity", {}) if isinstance(payload.get("identity_payload", {}), dict) else {}
    branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity, dict) else {}
    drift_risk = payload.get("drift_forecast", {}).get("risk", {}).get("blended_semantic_drift_risk", 0.0) if isinstance(payload.get("drift_forecast", {}), dict) else 0.0
    confidence_score = payload.get("confidence", {}).get("confidence_score", 0) if isinstance(payload.get("confidence", {}), dict) else 0
    stability_score = payload.get("stability_analysis", {}).get("stability_score", 0) if isinstance(payload.get("stability_analysis", {}), dict) else 0
    forms = payload.get("specialized_path", {}).get("forms", []) if isinstance(payload.get("specialized_path", {}), dict) else []
    final_identity_uri = ""
    if forms and isinstance(forms[0], dict):
        final_identity_uri = str(forms[0].get("final_identity_uri", ""))

    return {
        "label": label,
        "identity_uri": str(identity.get("identity_uri", "")),
        "semantic_tags": schema.get("semantic_tags", []),
        "drift_risk": float(drift_risk or 0.0),
        "branch_name": str(branch_resolution.get("selected_branch", "")),
        "confidence_score": int(confidence_score or 0),
        "stability_score": int(stability_score or 0),
        "final_identity_uri": final_identity_uri,
    }


def _redirect_to_admin_login(request):
    return redirect(f"{reverse('admin:login')}?next={request.get_full_path()}")


class ProjectMiddleLayerAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_admin_login(request)
        if not admin.site.has_permission(request):
            raise PermissionDenied
        if not has_semantic_capability(request.user, "view.semantic"):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def _audit_request(request, *, action: str, project: ProjectNode | None = None, payload: dict[str, object] | None = None, source: str = "admin"):
    record_semantic_audit_log(
        actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action,
        project=project,
        payload=payload or {},
        source=source,
    )


class ProjectMiddleLayerStatusView(View):
    def get(self, request):
        from project_middle_layer.pipelines import build_project_creation_payload

        payload = build_project_creation_payload(
            slug="project-middle-layer",
            name="Project Middle Layer",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            semantic_tags=["project", "semantic", "identity", "pipeline", "tier", "compiler"],
        )
        return JsonResponse(payload)


class ProjectMiddleLayerCompileView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_compile.html"
    form_class = ProjectMiddleLayerCompileForm
    success_url = "/admin/project-middle-layer/"

    def form_valid(self, form):
        if not has_semantic_capability(self.request.user, "compile.semantic"):
            raise PermissionDenied
        serializer = ProjectNodeWriteSerializer(
            data={
                "title": form.cleaned_data["title"],
                "intent": form.cleaned_data["intent"],
                "tier": form.cleaned_data["tier"],
                "tags": form.cleaned_data["tags"],
                "metadata": {
                    **({"description": form.cleaned_data["description"]} if form.cleaned_data.get("description") else {}),
                },
            }
        )
        serializer.is_valid(raise_exception=True)
        compiled, node = compile_and_store_project_node(serializer.validated_data)
        _audit_request(
            self.request,
            action="compile.semantic",
            project=node,
            payload={"slug": node.slug, "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", "")},
        )
        messages.success(
            self.request,
            f"Compiled {node.name} to {compiled['identity_payload']['identity']['identity_uri']}.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Compile Project Middle Layer"
        context["page_title"] = "Compile Project"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        return context

    def get_initial(self):
        initial = super().get_initial()
        for field in ["title", "intent", "tier", "tags", "description"]:
            value = self.request.GET.get(field)
            if value:
                initial[field] = value
        return initial


class ProjectMiddleLayerTimelineView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_timeline.html"

    def get(self, request):
        snapshots = list(
            ProjectEvolutionSnapshot.objects.select_related("project")[:100]
        )
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Evolution Timeline",
            "page_title": "Semantic Evolution Timeline",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "snapshots": snapshots,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerLineageExplorerView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_lineage.html"

    def get(self, request):
        lineage_records = list(SemanticLineageRecord.objects.select_related("project")[:100])
        project_cards = []

        for node in ProjectNode.objects.order_by("-updated_at")[:25]:
            metadata = node.metadata or {}
            semantic_tags = metadata.get("semantic_tags") or ["project", "semantic", "identity"]
            payload = build_project_creation_payload(
                slug=node.slug,
                name=node.name,
                semantic_intent=node.semantic_intent,
                mlas_tier=node.mlas_tier,
                btif_classification=node.btif_classification,
                semantic_tags=semantic_tags,
            )
            project_cards.append(
                {
                    "node": node,
                    "lineage_explorer": payload.get("lineage_explorer", {}),
                    "drift_heatmap_data": payload.get("drift_heatmap_data", {}),
                    "stability_analysis": payload.get("stability_analysis", {}),
                }
            )

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Lineage Explorer",
            "page_title": "Semantic Lineage Explorer",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "lineage_records": lineage_records,
            "project_cards": project_cards,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerAlertsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_alerts.html"

    def get(self, request):
        severity = (request.GET.get("severity") or "").strip().lower()
        alert_type = (request.GET.get("type") or "").strip().lower()

        alerts = SemanticAlert.objects.select_related("project", "source_snapshot").all()
        if severity:
            alerts = alerts.filter(severity=severity)
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)

        alerts = list(alerts[:100])
        summary = {
            "total": SemanticAlert.objects.count(),
            "high": SemanticAlert.objects.filter(severity="high").count(),
            "critical": SemanticAlert.objects.filter(severity="critical").count(),
            "types": {},
        }
        for item in SemanticAlert.objects.all()[:100]:
            summary["types"][item.alert_type] = summary["types"].get(item.alert_type, 0) + 1

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Alerts",
            "page_title": "Semantic Alerts",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "alerts": alerts,
            "summary": summary,
            "selected_severity": severity,
            "selected_type": alert_type,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerRecommendationsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_recommendations.html"

    def get(self, request):
        project_cards = []

        for node in ProjectNode.objects.order_by("-updated_at")[:25]:
            metadata = node.metadata or {}
            semantic_tags = metadata.get("semantic_tags") or ["project", "semantic", "identity"]
            payload = build_project_creation_payload(
                slug=node.slug,
                name=node.name,
                semantic_intent=node.semantic_intent,
                mlas_tier=node.mlas_tier,
                btif_classification=node.btif_classification,
                semantic_tags=semantic_tags,
            )
            recommendations = payload.get("recommendations", [])

            recommendation_actions = []
            for recommendation in recommendations:
                suggested_changes = recommendation.get("suggested_changes", {}) if isinstance(recommendation, dict) else {}
                tags = suggested_changes.get("tags") if isinstance(suggested_changes, dict) else None
                tags_value = ", ".join(tags) if isinstance(tags, list) and tags else ", ".join(semantic_tags)
                query = {
                    "title": node.name,
                    "intent": suggested_changes.get("intent", node.semantic_intent) if isinstance(suggested_changes, dict) else node.semantic_intent,
                    "tier": suggested_changes.get("tier", metadata.get("visibility_tier", "public")) if isinstance(suggested_changes, dict) else metadata.get("visibility_tier", "public"),
                    "tags": tags_value,
                    "description": metadata.get("description", ""),
                }
                recommendation_actions.append(
                    {
                        "label": recommendation.get("label", "Apply recommendation"),
                        "rationale": recommendation.get("rationale", ""),
                        "apply_url": f"{reverse('project_middle_layer:compile')}?{urlencode(query)}",
                    }
                )

            project_cards.append(
                {
                    "node": node,
                    "recommendations": recommendations,
                    "recommendation_actions": recommendation_actions,
                }
            )

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Recommendations",
            "page_title": "Semantic Recommendations",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "project_cards": project_cards,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerDiffView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_diff.html"

    def get(self, request):
        snapshot_a_id = request.GET.get("snapshot_a")
        snapshot_b_id = request.GET.get("snapshot_b")
        project_a_slug = request.GET.get("project_a")
        project_b_slug = request.GET.get("project_b")

        source_state = None
        target_state = None
        source_label = ""
        target_label = ""

        if snapshot_a_id and snapshot_b_id:
            try:
                source_snapshot = ProjectEvolutionSnapshot.objects.select_related("project").get(id=int(snapshot_a_id))
                target_snapshot = ProjectEvolutionSnapshot.objects.select_related("project").get(id=int(snapshot_b_id))
                source_state = _snapshot_to_diff_state(source_snapshot)
                target_state = _snapshot_to_diff_state(target_snapshot)
                source_label = f"{source_snapshot.project.name} snapshot {source_snapshot.id}"
                target_label = f"{target_snapshot.project.name} snapshot {target_snapshot.id}"
            except (ProjectEvolutionSnapshot.DoesNotExist, TypeError, ValueError):
                source_state = None
                target_state = None
        elif project_a_slug and project_b_slug:
            try:
                project_a = ProjectNode.objects.get(slug=project_a_slug)
                project_b = ProjectNode.objects.get(slug=project_b_slug)
                payload_a = build_project_creation_payload(
                    slug=project_a.slug,
                    name=project_a.name,
                    semantic_intent=project_a.semantic_intent,
                    mlas_tier=project_a.mlas_tier,
                    btif_classification=project_a.btif_classification,
                    semantic_tags=(project_a.metadata or {}).get("semantic_tags", ["project", "semantic", "identity"]),
                )
                payload_b = build_project_creation_payload(
                    slug=project_b.slug,
                    name=project_b.name,
                    semantic_intent=project_b.semantic_intent,
                    mlas_tier=project_b.mlas_tier,
                    btif_classification=project_b.btif_classification,
                    semantic_tags=(project_b.metadata or {}).get("semantic_tags", ["project", "semantic", "identity"]),
                )
                source_state = _payload_to_diff_state(payload_a, label=project_a.name)
                target_state = _payload_to_diff_state(payload_b, label=project_b.name)
                source_label = f"Project {project_a.name}"
                target_label = f"Project {project_b.name}"
            except ProjectNode.DoesNotExist:
                source_state = None
                target_state = None
        else:
            latest_two = list(ProjectEvolutionSnapshot.objects.select_related("project")[:2])
            if len(latest_two) == 2:
                source_snapshot = latest_two[1]
                target_snapshot = latest_two[0]
                source_state = _snapshot_to_diff_state(source_snapshot)
                target_state = _snapshot_to_diff_state(target_snapshot)
                source_label = f"{source_snapshot.project.name} snapshot {source_snapshot.id}"
                target_label = f"{target_snapshot.project.name} snapshot {target_snapshot.id}"

        diff_result = build_semantic_diff(source_state, target_state) if source_state and target_state else None

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Diff Viewer",
            "page_title": "Semantic Diff Viewer",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "diff_result": diff_result,
            "source_state": source_state,
            "target_state": target_state,
            "source_label": source_label,
            "target_label": target_label,
            "projects": list(ProjectNode.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


def _run_batch_compile(items: list[dict[str, object]], *, atomic_mode: bool) -> dict[str, object]:
    results: list[dict[str, object]] = []
    drift_values: list[float] = []
    confidence_values: list[int] = []
    compiled_count = 0
    failed_count = 0

    for index, item in enumerate(items):
        serializer = ProjectNodeWriteSerializer(data=item)
        if not serializer.is_valid():
            failed_count += 1
            results.append({"index": index, "status": "failed", "errors": serializer.errors})
            if atomic_mode:
                return {
                    "status": "rolled_back",
                    "results": results,
                    "summary": {
                        "requested": len(items),
                        "compiled": 0,
                        "failed": len(items),
                        "average_drift_risk": 0.0,
                        "average_confidence_score": 0.0,
                    },
                }
            continue

        compiled_payload, node = compile_and_store_project_node(serializer.validated_data)
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

    return {
        "status": "completed",
        "results": results,
        "summary": {
            "requested": len(items),
            "compiled": compiled_count,
            "failed": failed_count,
            "average_drift_risk": round(sum(drift_values) / len(drift_values), 4) if drift_values else 0.0,
            "average_confidence_score": round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0.0,
        },
    }


class ProjectMiddleLayerBatchCompileView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_batch_compile.html"
    form_class = ProjectMiddleLayerBatchCompileForm
    success_url = "/project-middle-layer/batch-compile/"

    def form_valid(self, form):
        if not has_semantic_capability(self.request.user, "compile.semantic"):
            raise PermissionDenied
        batch_result = _run_batch_compile(
            form.cleaned_data["payload_json"],
            atomic_mode=bool(form.cleaned_data.get("atomic", False)),
        )
        self._batch_result = batch_result
        _audit_request(
            self.request,
            action="batch.compile.semantic",
            payload={"status": batch_result.get("status"), "summary": batch_result.get("summary", {})},
        )

        if batch_result["status"] == "rolled_back":
            messages.error(self.request, "Batch compile rolled back due to validation errors in atomic mode.")
        else:
            summary = batch_result["summary"]
            messages.success(
                self.request,
                f"Batch compile complete. Compiled {summary['compiled']} of {summary['requested']} payloads.",
            )
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Batch Compile Project Middle Layer"
        context["page_title"] = "Batch Compile"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["batch_result"] = getattr(self, "_batch_result", None)
        return context


class ProjectMiddleLayerExportView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_export.html"
    form_class = ProjectMiddleLayerExportForm
    success_url = "/project-middle-layer/export/"

    def form_valid(self, form):
        if not has_semantic_capability(self.request.user, "export.semantic"):
            raise PermissionDenied
        payload = build_semantic_export_payload(
            scope=form.cleaned_data["scope"],
            project_slug=form.cleaned_data.get("project_slug"),
            include_history=bool(form.cleaned_data.get("include_history", False)),
            max_items=int(form.cleaned_data.get("max_items") or 100),
            exported_by=getattr(self.request.user, "username", "admin-user") or "admin-user",
        )

        if form.cleaned_data.get("download", True):
            stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
            scope_name = form.cleaned_data["scope"]
            if scope_name == "project":
                scope_name = form.cleaned_data.get("project_slug") or "project"
            filename = f"project-middle-layer-semantic-export-{scope_name}-{stamp}.json"
            body = export_payload_to_json(payload)
            response = HttpResponse(body, content_type="application/json")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            _audit_request(self.request, action="export.semantic", payload={"scope": form.cleaned_data["scope"], "download": True})
            return response

        self._export_payload = payload
        _audit_request(self.request, action="export.semantic", payload={"scope": form.cleaned_data["scope"], "download": False})
        messages.success(
            self.request,
            f"Semantic export generated for {payload['summary']['project_count']} project(s).",
        )
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Semantic Export Layer"
        context["page_title"] = "Semantic Export"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["export_payload"] = getattr(self, "_export_payload", None)
        return context


class ProjectMiddleLayerPipelinesView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_pipelines.html"
    form_class = ProjectMiddleLayerPipelineForm
    success_url = "/project-middle-layer/pipelines/"

    def form_valid(self, form):
        pipeline, _ = SemanticPipeline.objects.update_or_create(
            slug=form.cleaned_data["slug"],
            defaults={
                "name": form.cleaned_data["name"],
                "steps": form.cleaned_data["steps_json"],
                "triggers": form.cleaned_data["triggers_json"],
                "is_active": bool(form.cleaned_data.get("is_active", True)),
            },
        )
        messages.success(self.request, f"Pipeline '{pipeline.name}' saved.")
        return redirect(f"{reverse('project_middle_layer:pipelines')}?pipeline={pipeline.slug}")

    def get_initial(self):
        initial = super().get_initial()
        selected_slug = (self.request.GET.get("pipeline") or "").strip()
        if not selected_slug:
            return initial

        pipeline = SemanticPipeline.objects.filter(slug=selected_slug).first()
        if not pipeline:
            return initial

        import json

        initial.update(
            {
                "name": pipeline.name,
                "slug": pipeline.slug,
                "steps_json": json.dumps(pipeline.steps, indent=2),
                "triggers_json": json.dumps(pipeline.triggers, indent=2),
                "is_active": pipeline.is_active,
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_slug = (self.request.GET.get("pipeline") or "").strip()
        selected_pipeline = SemanticPipeline.objects.filter(slug=selected_slug).first() if selected_slug else None

        runs = []
        if selected_pipeline:
            runs = list(selected_pipeline.runs.all()[:25])

        context["title"] = "Semantic Pipelines"
        context["page_title"] = "Semantic Pipelines"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["pipelines"] = list(SemanticPipeline.objects.order_by("name")[:100])
        context["selected_pipeline"] = selected_pipeline
        context["selected_pipeline_runs"] = runs
        context["recent_runs"] = list(SemanticPipelineRun.objects.select_related("pipeline")[:20])
        return context


class ProjectMiddleLayerPipelineRunView(ProjectMiddleLayerAdminRequiredMixin, View):
    def post(self, request, slug: str):
        if not has_semantic_capability(request.user, "run.pipeline"):
            raise PermissionDenied
        pipeline = SemanticPipeline.objects.filter(slug=slug, is_active=True).first()
        if not pipeline:
            messages.error(request, "Active pipeline not found.")
            return redirect(reverse("project_middle_layer:pipelines"))

        run = run_semantic_pipeline(
            pipeline,
            triggered_by=getattr(request.user, "username", "admin-user") or "admin-user",
        )
        if run.status == "completed":
            messages.success(request, f"Pipeline '{pipeline.name}' completed.")
        else:
            messages.error(request, f"Pipeline '{pipeline.name}' failed: {run.error_message}")
        _audit_request(request, action="pipeline.run", payload={"pipeline_slug": pipeline.slug, "status": run.status})

        return redirect(f"{reverse('project_middle_layer:pipelines')}?pipeline={pipeline.slug}")


class ProjectMiddleLayerSchedulesView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_schedules.html"
    form_class = ProjectMiddleLayerScheduleForm
    success_url = "/project-middle-layer/schedules/"

    def form_valid(self, form):
        pipeline_slug = form.cleaned_data.get("pipeline_slug")
        pipeline = SemanticPipeline.objects.filter(slug=pipeline_slug).first() if pipeline_slug else None

        schedule, _ = SemanticSchedule.objects.update_or_create(
            slug=form.cleaned_data["slug"],
            defaults={
                "name": form.cleaned_data["name"],
                "cron_expression": form.cleaned_data["cron_expression"],
                "action": form.cleaned_data["action"],
                "pipeline": pipeline,
                "payload": form.cleaned_data["payload_json"],
                "is_paused": bool(form.cleaned_data.get("is_paused", False)),
                "status": "paused" if bool(form.cleaned_data.get("is_paused", False)) else "idle",
            },
        )
        messages.success(self.request, f"Schedule '{schedule.name}' saved.")
        return redirect(f"{reverse('project_middle_layer:schedules')}?schedule={schedule.slug}")

    def get_initial(self):
        initial = super().get_initial()
        selected_slug = (self.request.GET.get("schedule") or "").strip()
        if not selected_slug:
            return initial

        schedule = SemanticSchedule.objects.filter(slug=selected_slug).select_related("pipeline").first()
        if not schedule:
            return initial

        import json

        initial.update(
            {
                "name": schedule.name,
                "slug": schedule.slug,
                "cron_expression": schedule.cron_expression,
                "action": schedule.action,
                "pipeline_slug": schedule.pipeline.slug if schedule.pipeline else "",
                "payload_json": json.dumps(schedule.payload or {}, indent=2),
                "is_paused": schedule.is_paused,
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_slug = (self.request.GET.get("schedule") or "").strip()
        selected_schedule = SemanticSchedule.objects.filter(slug=selected_slug).select_related("pipeline").first() if selected_slug else None
        selected_runs = list(selected_schedule.runs.all()[:25]) if selected_schedule else []

        context["title"] = "Semantic Schedules"
        context["page_title"] = "Semantic Schedules"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["schedules"] = list(SemanticSchedule.objects.select_related("pipeline").order_by("name")[:100])
        context["selected_schedule"] = selected_schedule
        context["selected_schedule_runs"] = selected_runs
        context["recent_schedule_runs"] = list(SemanticScheduleRun.objects.select_related("schedule")[:20])
        return context


class ProjectMiddleLayerScheduleRunView(ProjectMiddleLayerAdminRequiredMixin, View):
    def post(self, request, slug: str):
        if not has_semantic_capability(request.user, "run.schedule"):
            raise PermissionDenied
        schedule = SemanticSchedule.objects.filter(slug=slug).first()
        if not schedule:
            messages.error(request, "Schedule not found.")
            return redirect(reverse("project_middle_layer:schedules"))

        run = run_semantic_schedule(
            schedule,
            triggered_by=getattr(request.user, "username", "admin-user") or "admin-user",
        )
        if run.status == "completed":
            messages.success(request, f"Schedule '{schedule.name}' completed.")
        else:
            messages.error(request, f"Schedule '{schedule.name}' failed: {run.error_message}")
        _audit_request(request, action="schedule.run", payload={"schedule_slug": schedule.slug, "status": run.status})
        return redirect(f"{reverse('project_middle_layer:schedules')}?schedule={schedule.slug}")


class ProjectMiddleLayerSchedulePauseView(ProjectMiddleLayerAdminRequiredMixin, View):
    def post(self, request, slug: str):
        schedule = SemanticSchedule.objects.filter(slug=slug).first()
        if not schedule:
            messages.error(request, "Schedule not found.")
            return redirect(reverse("project_middle_layer:schedules"))

        schedule.is_paused = not schedule.is_paused
        schedule.status = "paused" if schedule.is_paused else "idle"
        schedule.save(update_fields=["is_paused", "status", "updated_at"])

        if schedule.is_paused:
            messages.success(request, f"Schedule '{schedule.name}' paused.")
        else:
            messages.success(request, f"Schedule '{schedule.name}' resumed.")

        return redirect(f"{reverse('project_middle_layer:schedules')}?schedule={schedule.slug}")


class ProjectMiddleLayerWebhooksView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_webhooks.html"
    form_class = ProjectMiddleLayerWebhookForm
    success_url = "/project-middle-layer/webhooks/"

    def form_valid(self, form):
        webhook, _ = SemanticWebhook.objects.update_or_create(
            name=form.cleaned_data["name"],
            defaults={
                "target_url": form.cleaned_data["target_url"],
                "event_type": form.cleaned_data["event_type"],
                "secret_token": form.cleaned_data.get("secret_token", ""),
                "status": form.cleaned_data["status"],
            },
        )
        messages.success(self.request, f"Webhook '{webhook.name}' saved.")
        return redirect(f"{reverse('project_middle_layer:webhooks')}?webhook={webhook.id}")

    def get_initial(self):
        initial = super().get_initial()
        selected_id = (self.request.GET.get("webhook") or "").strip()
        if not selected_id:
            return initial
        try:
            webhook = SemanticWebhook.objects.get(id=int(selected_id))
        except (SemanticWebhook.DoesNotExist, ValueError, TypeError):
            return initial

        initial.update(
            {
                "name": webhook.name,
                "target_url": webhook.target_url,
                "event_type": webhook.event_type,
                "secret_token": webhook.secret_token,
                "status": webhook.status,
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = (self.request.GET.get("webhook") or "").strip()
        selected_webhook = None
        if selected_id:
            try:
                selected_webhook = SemanticWebhook.objects.get(id=int(selected_id))
            except (SemanticWebhook.DoesNotExist, ValueError, TypeError):
                selected_webhook = None

        deliveries = list(selected_webhook.deliveries.all()[:50]) if selected_webhook else []
        context["title"] = "Semantic Webhooks"
        context["page_title"] = "Semantic Webhooks"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["webhooks"] = list(SemanticWebhook.objects.order_by("name")[:100])
        context["selected_webhook"] = selected_webhook
        context["selected_deliveries"] = deliveries
        context["recent_deliveries"] = list(SemanticWebhookDelivery.objects.select_related("webhook")[:50])
        return context


class ProjectMiddleLayerWebhookRetryView(ProjectMiddleLayerAdminRequiredMixin, View):
    def post(self, request, delivery_id: int):
        if not has_semantic_capability(request.user, "retry.webhook"):
            raise PermissionDenied
        delivery = SemanticWebhookDelivery.objects.select_related("webhook").filter(id=delivery_id).first()
        if not delivery:
            messages.error(request, "Webhook delivery not found.")
            return redirect(reverse("project_middle_layer:webhooks"))

        retried = retry_webhook_delivery(delivery)
        if retried.status == "delivered":
            messages.success(request, f"Webhook delivery {retried.id} succeeded on retry.")
        else:
            messages.error(request, f"Webhook delivery {retried.id} retry failed: {retried.error_message}")
        _audit_request(request, action="webhook.retry", payload={"delivery_id": retried.id, "status": retried.status})

        return redirect(f"{reverse('project_middle_layer:webhooks')}?webhook={retried.webhook_id}")


class ProjectMiddleLayerIntegrationsView(ProjectMiddleLayerAdminRequiredMixin, FormView):
    template_name = "admin/project_middle_layer_integrations.html"
    form_class = ProjectMiddleLayerIntegrationForm
    success_url = "/project-middle-layer/integrations/"

    def form_valid(self, form):
        integration, _ = SemanticIntegration.objects.update_or_create(
            slug=form.cleaned_data["slug"],
            defaults={
                "name": form.cleaned_data["name"],
                "direction": form.cleaned_data["direction"],
                "target_system": form.cleaned_data["target_system"],
                "endpoint_url": form.cleaned_data.get("endpoint_url", ""),
                "api_key": form.cleaned_data["api_key"],
                "permissions": form.cleaned_data.get("permissions_csv", []),
                "status": form.cleaned_data["status"],
            },
        )
        messages.success(self.request, f"Integration '{integration.name}' saved.")
        return redirect(f"{reverse('project_middle_layer:integrations')}?integration={integration.slug}")

    def get_initial(self):
        initial = super().get_initial()
        selected_slug = (self.request.GET.get("integration") or "").strip()
        if not selected_slug:
            return initial

        integration = SemanticIntegration.objects.filter(slug=selected_slug).first()
        if not integration:
            return initial

        initial.update(
            {
                "name": integration.name,
                "slug": integration.slug,
                "direction": integration.direction,
                "target_system": integration.target_system,
                "endpoint_url": integration.endpoint_url,
                "api_key": integration.api_key,
                "permissions_csv": ", ".join(integration.permissions or []),
                "status": integration.status,
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_slug = (self.request.GET.get("integration") or "").strip()
        selected_integration = SemanticIntegration.objects.filter(slug=selected_slug).first() if selected_slug else None

        context["title"] = "Semantic Integrations"
        context["page_title"] = "Semantic Integrations"
        context["quick_action_back_url"] = reverse("admin:project-middle-layer-admin")
        context["integrations"] = list(SemanticIntegration.objects.order_by("name")[:100])
        context["selected_integration"] = selected_integration
        return context


class ProjectMiddleLayerIntegrationOutboundSyncView(ProjectMiddleLayerAdminRequiredMixin, View):
    def post(self, request, slug: str):
        if not has_semantic_capability(request.user, "sync.integration"):
            raise PermissionDenied
        integration = SemanticIntegration.objects.filter(slug=slug, status="active").first()
        if not integration:
            messages.error(request, "Active integration not found.")
            return redirect(reverse("project_middle_layer:integrations"))

        try:
            export_payload = run_outbound_integration_sync(
                integration=integration,
                scope="all",
                project_slug=None,
                include_history=False,
                max_items=100,
                triggered_by=getattr(request.user, "username", "admin-user") or "admin-user",
            )
            messages.success(
                request,
                f"Integration '{integration.name}' outbound sync completed for {export_payload.get('summary', {}).get('project_count', 0)} project(s).",
            )
            _audit_request(request, action="integration.sync.outbound", payload={"integration_slug": integration.slug, "project_count": export_payload.get("summary", {}).get("project_count", 0)})
        except Exception as exc:
            messages.error(request, f"Integration '{integration.name}' sync failed: {exc}")

        return redirect(f"{reverse('project_middle_layer:integrations')}?integration={integration.slug}")


class ProjectMiddleLayerAnalyticsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_analytics.html"

    def get(self, request):
        form = ProjectMiddleLayerAnalyticsForm(request.GET or None)
        branch_filter = ""
        tier_filter = ""
        limit = 30
        if form.is_valid():
            branch_filter = form.cleaned_data.get("branch_filter") or ""
            tier_filter = form.cleaned_data.get("tier_filter") or ""
            limit = int(form.cleaned_data.get("limit") or 30)

        dashboard = build_semantic_analytics_dashboard(
            limit=limit,
            branch_filter=branch_filter,
            tier_filter=tier_filter,
        )
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Analytics",
            "page_title": "Semantic Analytics",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "latest": dashboard.get("latest"),
            "trend_points": dashboard.get("trend_points", []),
            "available_branches": dashboard.get("available_branches", []),
            "available_tiers": dashboard.get("available_tiers", []),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "analytics.semantic"):
            raise PermissionDenied
        form = ProjectMiddleLayerAnalyticsForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid analytics filter input.")
            return redirect(reverse("project_middle_layer:analytics"))

        branch_filter = form.cleaned_data.get("branch_filter") or ""
        tier_filter = form.cleaned_data.get("tier_filter") or ""
        snapshot = build_semantic_analytics_snapshot(
            triggered_by=getattr(request.user, "username", "admin-user") or "admin-user",
            branch_filter=branch_filter,
            tier_filter=tier_filter,
        )
        _audit_request(request, action="analytics.snapshot", payload={"snapshot_id": snapshot.id, "branch_filter": branch_filter, "tier_filter": tier_filter})
        messages.success(request, f"Generated semantic analytics snapshot #{snapshot.id}.")
        query = f"?branch_filter={branch_filter}&tier_filter={tier_filter}" if (branch_filter or tier_filter) else ""
        return redirect(f"{reverse('project_middle_layer:analytics')}{query}")


class ProjectMiddleLayerDashboardView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_dashboard.html"

    def get(self, request):
        branch_filter = (request.GET.get("branch_filter") or "").strip()
        tier_filter = (request.GET.get("tier_filter") or "").strip()
        dashboard = build_semantic_analytics_dashboard(limit=20, branch_filter=branch_filter, tier_filter=tier_filter)
        context = {
            **admin.site.each_context(request),
            "title": "Semantic System Dashboard",
            "page_title": "Semantic System Dashboard",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "latest": dashboard.get("latest"),
            "trend_points": dashboard.get("trend_points", []),
            "filters": dashboard.get("filters", {}),
            "available_branches": dashboard.get("available_branches", []),
            "available_tiers": dashboard.get("available_tiers", []),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerSearchView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_search.html"

    def get(self, request):
        form = ProjectMiddleLayerSearchForm(request.GET or None)
        query = (request.GET.get("q") or "").strip()
        limit = 50
        if form.is_valid():
            query = form.cleaned_data.get("q") or ""
            limit = int(form.cleaned_data.get("limit") or 50)

        result = run_semantic_search(query, limit=limit) if query else None
        if query:
            _audit_request(request, action="search.semantic", payload={"query": query, "limit": limit})
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Search",
            "page_title": "Semantic Search",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "query": query,
            "result": result,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerInsightsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_insights.html"

    def get(self, request):
        _audit_request(request, action="insights.semantic")
        insights = build_semantic_insights(limit=20)
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Insights",
            "page_title": "Semantic Insights",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "insights": insights,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerAgentsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_agents.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Agents",
            "page_title": "Semantic Agents",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "agent_names": AGENT_NAMES,
            "latest_run": SemanticAgentRun.objects.first(),
            "runs": list(SemanticAgentRun.objects.all()[:50]),
            "form": ProjectMiddleLayerAgentRunForm(),
            "snapshot_count": SemanticAnalyticsSnapshot.objects.count(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "run.agent"):
            raise PermissionDenied
        form = ProjectMiddleLayerAgentRunForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid agent selection.")
            return redirect(reverse("project_middle_layer:agents"))

        agent_name = form.cleaned_data["agent_name"]
        try:
            run = run_semantic_agent(agent_name)
            _audit_request(request, action="agent.run", payload={"agent_name": agent_name, "run_id": run.id, "status": run.status})
            messages.success(request, f"{agent_name} completed (run #{run.id}).")
        except Exception as exc:
            messages.error(request, f"{agent_name} failed: {exc}")
        return redirect(reverse("project_middle_layer:agents"))


class ProjectMiddleLayerRolesView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_roles.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Roles",
            "page_title": "Semantic Roles",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "role_form": SemanticRoleForm(),
            "permission_form": SemanticPermissionForm(),
            "roles": list(SemanticRole.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        if action == "create-role":
            if not has_semantic_capability(request.user, "manage.roles"):
                raise PermissionDenied
            role_form = SemanticRoleForm(request.POST)
            permission_form = SemanticPermissionForm()
            if role_form.is_valid():
                capabilities = role_form.cleaned_data["capabilities_csv"]
                role, _ = SemanticRole.objects.update_or_create(
                    slug=role_form.cleaned_data["slug"],
                    defaults={
                        "name": role_form.cleaned_data["name"],
                        "capabilities": capabilities,
                    },
                )
                _audit_request(request, action="role.upsert", payload={"role_slug": role.slug, "capabilities": capabilities})
                messages.success(request, f"Role '{role.name}' saved.")
                return redirect(reverse("project_middle_layer:roles"))
        elif action == "assign-permission":
            if not has_semantic_capability(request.user, "manage.roles"):
                raise PermissionDenied
            role_form = SemanticRoleForm()
            permission_form = SemanticPermissionForm(request.POST)
            if permission_form.is_valid():
                actor = resolve_actor_by_username(permission_form.cleaned_data["username"])
                role = SemanticRole.objects.filter(slug=permission_form.cleaned_data["role_slug"]).first()
                project_slug = (permission_form.cleaned_data.get("project_slug") or "").strip()
                project = ProjectNode.objects.filter(slug=project_slug).first() if project_slug else None
                if not actor:
                    messages.error(request, "User not found.")
                elif not role:
                    messages.error(request, "Role not found.")
                else:
                    SemanticPermission.objects.create(
                        role=role,
                        user=actor,
                        project=project,
                        tier=(permission_form.cleaned_data.get("tier") or "").strip().lower(),
                        branch=(permission_form.cleaned_data.get("branch") or "").strip().lower(),
                    )
                    _audit_request(
                        request,
                        action="permission.assign",
                        project=project,
                        payload={"username": actor.username, "role_slug": role.slug},
                    )
                    messages.success(request, f"Permission assigned to {actor.username}.")
                    return redirect(reverse("project_middle_layer:roles"))
        else:
            role_form = SemanticRoleForm()
            permission_form = SemanticPermissionForm()

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Roles",
            "page_title": "Semantic Roles",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "role_form": role_form,
            "permission_form": permission_form,
            "roles": list(SemanticRole.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerCollaborationView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_collaboration.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Collaboration",
            "page_title": "Semantic Collaboration",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "session_form": SemanticEditSessionForm(),
            "sessions": list(SemanticEditSession.objects.select_related("project", "user")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "edit.semantic"):
            raise PermissionDenied
        form = SemanticEditSessionForm(request.POST)
        if form.is_valid():
            project = ProjectNode.objects.filter(slug=form.cleaned_data["project_slug"]).first()
            if not project:
                messages.error(request, "Project not found.")
            else:
                try:
                    session = acquire_edit_session(
                        project=project,
                        user=request.user,
                        force_takeover=bool(form.cleaned_data.get("force_takeover", False)),
                    )
                    _audit_request(request, action="edit.session.acquire", project=project, payload={"session_id": session.id})
                    messages.success(request, f"Edit session #{session.id} acquired for {project.slug}.")
                    return redirect(reverse("project_middle_layer:collaboration"))
                except ValueError as exc:
                    messages.error(request, str(exc))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Collaboration",
            "page_title": "Semantic Collaboration",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "session_form": form,
            "sessions": list(SemanticEditSession.objects.select_related("project", "user")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerChangeRequestsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_change_requests.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Change Requests",
            "page_title": "Semantic Change Requests",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "change_form": SemanticChangeRequestForm(),
            "review_form": SemanticChangeReviewForm(),
            "change_requests": list(SemanticChangeRequest.objects.select_related("project", "author", "reviewer")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        change_form = SemanticChangeRequestForm()
        review_form = SemanticChangeReviewForm()

        if action == "create-change-request":
            if not has_semantic_capability(request.user, "review.request"):
                raise PermissionDenied
            change_form = SemanticChangeRequestForm(request.POST)
            if change_form.is_valid():
                project = ProjectNode.objects.filter(slug=change_form.cleaned_data["project_slug"]).first()
                if not project:
                    messages.error(request, "Project not found.")
                else:
                    request_obj = create_change_request(
                        project=project,
                        author=request.user,
                        proposed_changes=change_form.cleaned_data["proposed_changes_json"],
                    )
                    _audit_request(request, action="change.request.create", project=project, payload={"change_request_id": request_obj.id})
                    messages.success(request, f"Change request #{request_obj.id} created.")
                    return redirect(reverse("project_middle_layer:change-requests"))
        elif action == "review-change-request":
            if not has_semantic_capability(request.user, "review.approve"):
                raise PermissionDenied
            review_form = SemanticChangeReviewForm(request.POST)
            if review_form.is_valid():
                change_request = SemanticChangeRequest.objects.filter(id=review_form.cleaned_data["change_request_id"]).first()
                if not change_request:
                    messages.error(request, "Change request not found.")
                else:
                    updated = apply_change_request(
                        change_request=change_request,
                        reviewer=request.user,
                        approve=bool(review_form.cleaned_data.get("approve", False)),
                        notes=review_form.cleaned_data.get("notes", ""),
                    )
                    _audit_request(request, action="change.request.review", project=updated.project, payload={"change_request_id": updated.id, "status": updated.status})
                    messages.success(request, f"Change request #{updated.id} {updated.status}.")
                    return redirect(reverse("project_middle_layer:change-requests"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Change Requests",
            "page_title": "Semantic Change Requests",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "change_form": change_form,
            "review_form": review_form,
            "change_requests": list(SemanticChangeRequest.objects.select_related("project", "author", "reviewer")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerAuditView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_audit.html"

    def get(self, request):
        form = SemanticAuditFilterForm(request.GET or None)
        logs = SemanticAuditLog.objects.select_related("actor", "project").all()
        if form.is_valid():
            actor_username = (form.cleaned_data.get("actor_username") or "").strip()
            action = (form.cleaned_data.get("action") or "").strip()
            project_slug = (form.cleaned_data.get("project_slug") or "").strip()
            source = (form.cleaned_data.get("source") or "").strip()
            if actor_username:
                logs = logs.filter(actor__username=actor_username)
            if action:
                logs = logs.filter(action=action)
            if project_slug:
                logs = logs.filter(project__slug=project_slug)
            if source:
                logs = logs.filter(source=source)

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Audit Logs",
            "page_title": "Semantic Audit Logs",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "filter_form": form,
            "logs": list(logs[:200]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerVersionsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_versions.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Versions",
            "page_title": "Semantic Versions",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "commit_form": SemanticVersionCommitForm(),
            "checkout_form": SemanticVersionCheckoutForm(),
            "versions": list(SemanticVersion.objects.select_related("project", "author", "snapshot")[:200]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        commit_form = SemanticVersionCommitForm()
        checkout_form = SemanticVersionCheckoutForm()

        if action == "commit-version":
            if not has_semantic_capability(request.user, "version.commit"):
                raise PermissionDenied
            commit_form = SemanticVersionCommitForm(request.POST)
            if commit_form.is_valid():
                project = ProjectNode.objects.filter(slug=commit_form.cleaned_data["project_slug"]).first()
                if not project:
                    messages.error(request, "Project not found.")
                else:
                    version = commit_semantic_version(project=project, author=request.user, message=commit_form.cleaned_data.get("message", ""))
                    _audit_request(request, action="version.commit", project=project, payload={"version_id": version.id, "version_number": version.version_number})
                    messages.success(request, f"Committed semantic version v{version.version_number}.")
                    return redirect(reverse("project_middle_layer:versions"))
        elif action == "checkout-version":
            if not has_semantic_capability(request.user, "version.checkout"):
                raise PermissionDenied
            checkout_form = SemanticVersionCheckoutForm(request.POST)
            if checkout_form.is_valid():
                version = SemanticVersion.objects.filter(id=checkout_form.cleaned_data["version_id"]).select_related("project").first()
                if not version:
                    messages.error(request, "Version not found.")
                else:
                    project = checkout_semantic_version(version=version, actor=request.user)
                    _audit_request(request, action="version.checkout", project=project, payload={"version_id": version.id, "version_number": version.version_number})
                    messages.success(request, f"Checked out semantic version v{version.version_number}.")
                    return redirect(reverse("project_middle_layer:versions"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Versions",
            "page_title": "Semantic Versions",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "commit_form": commit_form,
            "checkout_form": checkout_form,
            "versions": list(SemanticVersion.objects.select_related("project", "author", "snapshot")[:200]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerMergeView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_merge.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Merge Resolution",
            "page_title": "Semantic Merge Resolution",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "left_json": "{}",
            "right_json": "{}",
            "base_json": "{}",
            "merge_result": None,
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "merge.semantic"):
            raise PermissionDenied
        left_json = (request.POST.get("left_json") or "{}").strip()
        right_json = (request.POST.get("right_json") or "{}").strip()
        base_json = (request.POST.get("base_json") or "{}").strip()
        merge_result = None
        try:
            left = json.loads(left_json or "{}")
            right = json.loads(right_json or "{}")
            base = json.loads(base_json or "{}")
            if not isinstance(left, dict) or not isinstance(right, dict) or not isinstance(base, dict):
                raise ValueError("Merge JSON inputs must be objects.")
            merge_result = merge_semantic_states(left, right, base=base)
            _audit_request(request, action="merge.semantic", payload={"has_conflicts": merge_result.get("has_conflicts", False)})
            messages.success(request, "Merge computed.")
        except Exception as exc:
            messages.error(request, f"Invalid merge payload: {exc}")

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Merge Resolution",
            "page_title": "Semantic Merge Resolution",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "left_json": left_json,
            "right_json": right_json,
            "base_json": base_json,
            "merge_result": merge_result,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerReplicationView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_replication.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Replication",
            "page_title": "Semantic Replication",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": ReplicationConfigForm(),
            "targets": list(ReplicationConfig.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        form = ReplicationConfigForm(request.POST)
        if action == "save" and form.is_valid():
            target, _ = ReplicationConfig.objects.update_or_create(
                slug=form.cleaned_data["slug"],
                defaults={
                    "name": form.cleaned_data["name"],
                    "remote_node_url": form.cleaned_data["remote_node_url"],
                    "api_key": form.cleaned_data["api_key"],
                    "mode": form.cleaned_data["mode"],
                    "direction": form.cleaned_data["direction"],
                    "is_active": bool(form.cleaned_data.get("is_active", True)),
                },
            )
            _audit_request(request, action="replication.target.upsert", payload={"slug": target.slug})
            messages.success(request, f"Replication target '{target.name}' saved.")
            return redirect(reverse("project_middle_layer:replication"))

        if action == "sync":
            slug = (request.POST.get("target_slug") or "").strip()
            target = ReplicationConfig.objects.filter(slug=slug).first()
            if target:
                result = run_replication(target, direction=target.direction)
                _audit_request(request, action="replication.sync", payload={"slug": slug, "synced_versions": result.get("synced_versions", 0)})
                messages.success(request, f"Replication sync for '{slug}' completed.")
            else:
                messages.error(request, "Replication target not found.")
            return redirect(reverse("project_middle_layer:replication"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Replication",
            "page_title": "Semantic Replication",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "targets": list(ReplicationConfig.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerFederationView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_federation.html"

    def get(self, request):
        query = (request.GET.get("q") or "").strip()
        federated_result = run_federated_search(query, limit=30) if query else None
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Federation",
            "page_title": "Semantic Federation",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": FederationPeerForm(),
            "peers": list(FederationPeer.objects.order_by("name")[:100]),
            "query": query,
            "federated_result": federated_result,
            "federated_insights": run_federated_insights(limit=10),
            "lineage_cluster_map": run_federated_lineage_cluster_mapping(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        form = FederationPeerForm(request.POST)
        if form.is_valid():
            peer, _ = FederationPeer.objects.update_or_create(
                slug=form.cleaned_data["slug"],
                defaults={
                    "name": form.cleaned_data["name"],
                    "peer_identity": form.cleaned_data["peer_identity"],
                    "peer_url": form.cleaned_data["peer_url"],
                    "capabilities": form.cleaned_data["capabilities_csv"],
                    "sync_rules": form.cleaned_data["sync_rules_json"],
                    "is_active": bool(form.cleaned_data.get("is_active", True)),
                },
            )
            _audit_request(request, action="federation.peer.upsert", payload={"slug": peer.slug})
            messages.success(request, f"Federation peer '{peer.name}' saved.")
            return redirect(reverse("project_middle_layer:federation"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Federation",
            "page_title": "Semantic Federation",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "peers": list(FederationPeer.objects.order_by("name")[:100]),
            "query": "",
            "federated_result": None,
            "federated_insights": run_federated_insights(limit=10),
            "lineage_cluster_map": run_federated_lineage_cluster_mapping(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerShardsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_shards.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Sharding",
            "page_title": "Semantic Sharding",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticShardForm(),
            "shards": list(SemanticShard.objects.order_by("name")[:100]),
            "shard_map": build_shard_map(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        if action == "rebalance":
            result = rebalance_shards()
            _audit_request(request, action="sharding.rebalance", payload=result)
            messages.success(request, "Shard rebalance completed.")
            return redirect(reverse("project_middle_layer:shards"))

        form = SemanticShardForm(request.POST)
        if form.is_valid():
            strategy = form.cleaned_data["strategy"]
            route_value = (form.cleaned_data.get("route_value") or "").strip()
            defaults = {
                "name": form.cleaned_data["name"],
                "node_url": form.cleaned_data.get("node_url", ""),
                "strategy": strategy,
                "route_value": route_value,
                "is_active": bool(form.cleaned_data.get("is_active", True)),
                "branch": route_value if strategy == "branch" else "",
                "tier": route_value if strategy == "tier" else "",
                "project_slug_prefix": route_value if strategy == "slug_prefix" else "",
                "cluster_label": route_value if strategy == "cluster" else "",
            }
            shard, _ = SemanticShard.objects.update_or_create(slug=form.cleaned_data["slug"], defaults=defaults)
            _audit_request(request, action="shard.upsert", payload={"slug": shard.slug, "strategy": shard.strategy})
            messages.success(request, f"Shard '{shard.name}' saved.")
            return redirect(reverse("project_middle_layer:shards"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Sharding",
            "page_title": "Semantic Sharding",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "shards": list(SemanticShard.objects.order_by("name")[:100]),
            "shard_map": build_shard_map(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerCacheView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_cache.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Cache",
            "page_title": "Semantic Cache",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticCacheControlForm(),
            "cache_result": None,
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        action = (request.POST.get("action") or "").strip()
        cache_result = None
        form = SemanticCacheControlForm(request.POST)

        if action == "flush":
            cache_result = flush_semantic_cache()
            _audit_request(request, action="cache.flush", payload=cache_result)
            messages.success(request, "Semantic cache flushed.")
        elif action == "warm":
            cache_result = warm_semantic_cache()
            _audit_request(request, action="cache.warm", payload=cache_result)
            messages.success(request, "Semantic cache warmed.")
        elif form.is_valid():
            cache_result = get_or_set_cached(form.cleaned_data["target"], form.cleaned_data["params_json"], ttl_seconds=600)
            _audit_request(request, action="cache.inspect", payload={"target": form.cleaned_data["target"], "cached": cache_result.get("cached")})
            messages.success(request, "Cache inspect completed.")

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Cache",
            "page_title": "Semantic Cache",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "cache_result": cache_result,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerSyncView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_sync.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Sync",
            "page_title": "Semantic Sync",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticSyncForm(),
            "logs": list(SemanticSyncLog.objects.order_by("-started_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        form = SemanticSyncForm(request.POST)
        if form.is_valid():
            result = run_semantic_sync(
                sync_type=form.cleaned_data["sync_type"],
                target_slug=form.cleaned_data.get("target_slug") or None,
            )
            _audit_request(request, action="sync.semantic", payload=result)
            messages.success(request, f"Sync run completed with status: {result.get('status', 'unknown')}.")
            return redirect(reverse("project_middle_layer:sync"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Sync",
            "page_title": "Semantic Sync",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "logs": list(SemanticSyncLog.objects.order_by("-started_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerDistributedAgentsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_distributed_agents.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Distributed Semantic Agents",
            "page_title": "Distributed Semantic Agents",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": DistributedAgentRunForm(),
            "agent_names": DISTRIBUTED_AGENT_NAMES,
            "runs": list(DistributedAgentRun.objects.order_by("-created_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        form = DistributedAgentRunForm(request.POST)
        if form.is_valid():
            run = run_distributed_agent(form.cleaned_data["agent_name"])
            _audit_request(request, action="agent.distributed.run", payload={"run_id": run.id, "agent_name": run.agent_name, "status": run.status})
            messages.success(request, f"Distributed agent '{run.agent_name}' completed (run #{run.id}).")
            return redirect(reverse("project_middle_layer:distributed-agents"))

        context = {
            **admin.site.each_context(request),
            "title": "Distributed Semantic Agents",
            "page_title": "Distributed Semantic Agents",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "agent_names": DISTRIBUTED_AGENT_NAMES,
            "runs": list(DistributedAgentRun.objects.order_by("-created_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerMarketplaceView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_marketplace.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Marketplace",
            "page_title": "Semantic Marketplace",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": MarketplaceInstallForm(),
            "items": list(MarketplaceItem.objects.order_by("name")[:100]),
            "installs": list(MarketplaceInstall.objects.select_related("item", "owner")[:100]),
            "update_notifications": build_marketplace_update_notifications(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "manage.marketplace"):
            raise PermissionDenied
        form = MarketplaceInstallForm(request.POST)
        if form.is_valid():
            try:
                result = install_marketplace_item(
                    item_slug=form.cleaned_data["item_slug"],
                    requested_version=(form.cleaned_data.get("requested_version") or "").strip() or None,
                    owner=request.user,
                )
                _audit_request(request, action="marketplace.install", payload=result)
                messages.success(request, f"Marketplace item '{result['item_slug']}' installed.")
                return redirect(reverse("project_middle_layer:marketplace"))
            except ValueError as exc:
                messages.error(request, str(exc))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Marketplace",
            "page_title": "Semantic Marketplace",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "items": list(MarketplaceItem.objects.order_by("name")[:100]),
            "installs": list(MarketplaceInstall.objects.select_related("item", "owner")[:100]),
            "update_notifications": build_marketplace_update_notifications(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerPluginsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_plugins.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Plugins",
            "page_title": "Semantic Plugins",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticPluginForm(),
            "plugins": list(SemanticPlugin.objects.order_by("name")[:100]),
            "registry": load_plugin_registry(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "manage.plugins"):
            raise PermissionDenied
        action = (request.POST.get("action") or "").strip()

        if action == "toggle":
            slug = (request.POST.get("plugin_slug") or "").strip()
            enabled = bool(request.POST.get("enabled") == "1")
            try:
                plugin = set_plugin_enabled(slug=slug, enabled=enabled)
                _audit_request(request, action="plugin.toggle", payload={"plugin_slug": plugin.slug, "enabled": plugin.enabled})
                messages.success(request, f"Plugin '{plugin.slug}' updated.")
            except ValueError as exc:
                messages.error(request, str(exc))
            return redirect(reverse("project_middle_layer:plugins"))

        form = SemanticPluginForm(request.POST)
        if form.is_valid():
            plugin = register_plugin(
                {
                    "name": form.cleaned_data["name"],
                    "slug": form.cleaned_data["slug"],
                    "plugin_type": form.cleaned_data["plugin_type"],
                    "entrypoint": form.cleaned_data["entrypoint"],
                    "capabilities": form.cleaned_data["capabilities_csv"],
                    "version": form.cleaned_data.get("version") or "0.0.1",
                }
            )
            set_plugin_enabled(slug=plugin.slug, enabled=bool(form.cleaned_data.get("enabled", False)))
            _audit_request(request, action="plugin.upsert", payload={"plugin_slug": plugin.slug})
            messages.success(request, f"Plugin '{plugin.name}' saved.")
            return redirect(reverse("project_middle_layer:plugins"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Plugins",
            "page_title": "Semantic Plugins",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "plugins": list(SemanticPlugin.objects.order_by("name")[:100]),
            "registry": load_plugin_registry(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerExtensionsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_extensions.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Semantic Extensions",
            "page_title": "Semantic Extensions",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticExtensionForm(),
            "extensions": list(SemanticExtension.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "manage.extensions"):
            raise PermissionDenied
        action = (request.POST.get("action") or "").strip()

        if action in {"apply", "rollback"}:
            slug = (request.POST.get("extension_slug") or "").strip()
            try:
                result = apply_semantic_extension(extension_slug=slug) if action == "apply" else rollback_semantic_extension(extension_slug=slug)
                _audit_request(request, action=f"extension.{action}", payload=result)
                messages.success(request, f"Extension action '{action}' completed for '{slug}'.")
            except ValueError as exc:
                messages.error(request, str(exc))
            return redirect(reverse("project_middle_layer:extensions"))

        form = SemanticExtensionForm(request.POST)
        if form.is_valid():
            extension, _ = SemanticExtension.objects.update_or_create(
                slug=form.cleaned_data["slug"],
                defaults={
                    "name": form.cleaned_data["name"],
                    "version": form.cleaned_data.get("version") or "0.0.1",
                    "schema_patch": form.cleaned_data["schema_patch_json"],
                    "rules_patch": form.cleaned_data["rules_patch_json"],
                },
            )
            _audit_request(request, action="extension.upsert", payload={"extension_slug": extension.slug})
            messages.success(request, f"Extension '{extension.name}' saved.")
            return redirect(reverse("project_middle_layer:extensions"))

        context = {
            **admin.site.each_context(request),
            "title": "Semantic Extensions",
            "page_title": "Semantic Extensions",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "extensions": list(SemanticExtension.objects.order_by("name")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerGatewayView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_gateway.html"

    def get(self, request):
        form = SemanticGatewayForm(request.GET or None)
        dispatch = None
        if form.is_valid() and form.cleaned_data.get("route"):
            dispatch = gateway_dispatch(
                route=form.cleaned_data["route"],
                requested_version=form.cleaned_data.get("requested_version"),
            )
        context = {
            **admin.site.each_context(request),
            "title": "Semantic API Gateway",
            "page_title": "Semantic API Gateway",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "dispatch": dispatch,
            "route_map": gateway_route_map(),
            "schema": gateway_schema_introspection(),
            "health": gateway_health_status(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerBtifPlusView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_btif_plus.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "BTIF+ Interoperability",
            "page_title": "BTIF+ Interoperability",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": BtifPlusForm(),
            "payload": None,
            "validation": None,
            "compatibility": btif_plus_compatibility_matrix(),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "btif.interop"):
            raise PermissionDenied
        action = (request.POST.get("action") or "").strip()
        form = BtifPlusForm(request.POST)
        payload = None
        validation = None

        if form.is_valid():
            try:
                if action == "export":
                    payload = encode_btif_plus(project_slug=form.cleaned_data["project_slug"])
                    validation = validate_btif_plus(payload)
                elif action == "validate":
                    payload = decode_btif_plus(form.cleaned_data.get("payload_json") or {})
                    validation = validate_btif_plus(payload)
                _audit_request(request, action=f"btif.{action or 'inspect'}", payload={"project_slug": form.cleaned_data["project_slug"], "valid": bool(validation and validation.get("valid"))})
                messages.success(request, "BTIF+ action completed.")
            except ValueError as exc:
                messages.error(request, str(exc))

        context = {
            **admin.site.each_context(request),
            "title": "BTIF+ Interoperability",
            "page_title": "BTIF+ Interoperability",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "payload": payload,
            "validation": validation,
            "compatibility": btif_plus_compatibility_matrix(),
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerExternalAgentsView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_external_agents.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "External Semantic Agents",
            "page_title": "External Semantic Agents",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": ExternalAgentForm(),
            "agents": list(ExternalAgent.objects.order_by("name")[:100]),
            "run_result": None,
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "manage.external_agents"):
            raise PermissionDenied
        action = (request.POST.get("action") or "").strip()
        run_result = None

        if action == "run":
            slug = (request.POST.get("agent_slug") or "").strip()
            operation = (request.POST.get("operation") or "").strip()
            try:
                run_result = run_external_agent(agent_slug=slug, operation=operation, payload={"triggered_by": request.user.username})
                _audit_request(request, action="external.agent.run", payload=run_result)
                messages.success(request, f"External agent '{slug}' completed operation '{operation}'.")
            except ValueError as exc:
                messages.error(request, str(exc))
            context = {
                **admin.site.each_context(request),
                "title": "External Semantic Agents",
                "page_title": "External Semantic Agents",
                "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
                "form": ExternalAgentForm(),
                "agents": list(ExternalAgent.objects.order_by("name")[:100]),
                "run_result": run_result,
            }
            return TemplateResponse(request, self.template_name, context)

        form = ExternalAgentForm(request.POST)
        if form.is_valid():
            agent = register_external_agent(
                {
                    "name": form.cleaned_data["name"],
                    "slug": form.cleaned_data["slug"],
                    "endpoint": form.cleaned_data["endpoint"],
                    "capabilities": form.cleaned_data["capabilities_csv"],
                    "auth_token": form.cleaned_data.get("auth_token", ""),
                    "status": form.cleaned_data["status"],
                }
            )
            _audit_request(request, action="external.agent.register", payload={"agent_slug": agent.slug})
            messages.success(request, f"External agent '{agent.name}' saved.")
            return redirect(reverse("project_middle_layer:external-agents"))

        context = {
            **admin.site.each_context(request),
            "title": "External Semantic Agents",
            "page_title": "External Semantic Agents",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "agents": list(ExternalAgent.objects.order_by("name")[:100]),
            "run_result": None,
        }
        return TemplateResponse(request, self.template_name, context)


class ProjectMiddleLayerCrossSyncView(ProjectMiddleLayerAdminRequiredMixin, View):
    template_name = "admin/project_middle_layer_cross_sync.html"

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            "title": "Cross-Platform Semantic Sync",
            "page_title": "Cross-Platform Semantic Sync",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": SemanticCrossSyncForm(),
            "logs": list(SemanticCrossSyncLog.objects.order_by("-started_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request):
        if not has_semantic_capability(request.user, "sync.cross_platform"):
            raise PermissionDenied
        form = SemanticCrossSyncForm(request.POST)
        if form.is_valid():
            result = run_semantic_cross_sync(
                sync_type=form.cleaned_data["sync_type"],
                target_platform=form.cleaned_data["target_platform"],
                project_slug=form.cleaned_data["project_slug"],
            )
            _audit_request(request, action="sync.cross_platform", payload=result)
            messages.success(request, f"Cross-platform sync completed with status: {result.get('status', 'unknown')}.")
            return redirect(reverse("project_middle_layer:cross-sync"))

        context = {
            **admin.site.each_context(request),
            "title": "Cross-Platform Semantic Sync",
            "page_title": "Cross-Platform Semantic Sync",
            "quick_action_back_url": reverse("admin:project-middle-layer-admin"),
            "form": form,
            "logs": list(SemanticCrossSyncLog.objects.order_by("-started_at")[:100]),
        }
        return TemplateResponse(request, self.template_name, context)
