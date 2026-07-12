import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from project_middle_layer.api.serializers import ProjectNodeWriteSerializer
from project_middle_layer.audit import record_semantic_audit_log
from project_middle_layer.api_gateway import gateway_dispatch, gateway_health_status, gateway_route_map, gateway_schema_introspection
from project_middle_layer.btif_plus import decode_btif_plus, encode_btif_plus, validate_btif_plus
from project_middle_layer.extensions import apply_semantic_extension, rollback_semantic_extension
from project_middle_layer.external_agents import register_external_agent, run_external_agent
from project_middle_layer.exports import build_semantic_export_payload
from project_middle_layer.marketplace import install_marketplace_item
from project_middle_layer.models import ProjectNode, SemanticPipeline, SemanticSchedule, SemanticVersion
from project_middle_layer.permissions import has_semantic_capability, resolve_actor_by_username
from project_middle_layer.pipelines import run_semantic_pipeline
from project_middle_layer.schedules import run_semantic_schedule
from project_middle_layer.semantic_cross_sync import run_semantic_cross_sync
from project_middle_layer.semantic import build_semantic_diff
from project_middle_layer.semantic_merge import merge_semantic_states
from project_middle_layer.services import compile_and_store_project_node
from project_middle_layer.versioning import checkout_semantic_version, commit_semantic_version


class Command(BaseCommand):
    help = "Run semantic Project Middle Layer CLI operations."

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=[
                "compile",
                "batch-compile",
                "diff",
                "export",
                "pipeline-run",
                "schedule-run",
                "version-commit",
                "version-checkout",
                "merge",
                "marketplace-install",
                "gateway-introspect",
                "gateway-dispatch",
                "btif-export",
                "btif-validate",
                "extension-apply",
                "extension-rollback",
                "external-agent-register",
                "external-agent-run",
                "cross-sync-run",
            ],
            help="CLI operation to execute.",
        )
        parser.add_argument("--payload-json", type=str, default="", help="JSON payload for compile or batch-compile.")
        parser.add_argument("--source-json", type=str, default="", help="Source JSON payload for diff.")
        parser.add_argument("--target-json", type=str, default="", help="Target JSON payload for diff.")
        parser.add_argument("--scope", choices=["all", "project"], default="all", help="Export scope.")
        parser.add_argument("--project-slug", type=str, default="", help="Project slug for project-scoped export.")
        parser.add_argument("--include-history", action="store_true", help="Include history in export payload.")
        parser.add_argument("--max-items", type=int, default=100, help="Maximum items for export.")
        parser.add_argument("--pipeline-slug", type=str, default="", help="Pipeline slug for pipeline-run.")
        parser.add_argument("--schedule-slug", type=str, default="", help="Schedule slug for schedule-run.")
        parser.add_argument("--version-id", type=int, default=0, help="Version ID for version-checkout.")
        parser.add_argument("--message", type=str, default="", help="Message for version-commit.")
        parser.add_argument("--atomic", action="store_true", help="Atomic mode for batch compile.")
        parser.add_argument("--triggered-by", type=str, default="cli", help="Actor label for runs and exports.")
        parser.add_argument("--actor-username", type=str, default="", help="Optional username for permission checks and audit attribution.")
        parser.add_argument("--item-slug", type=str, default="", help="Marketplace item slug for marketplace-install.")
        parser.add_argument("--requested-version", type=str, default="", help="Requested marketplace version.")
        parser.add_argument("--route", type=str, default="", help="Gateway route for gateway-dispatch.")
        parser.add_argument("--gateway-version", type=str, default="v1", help="Gateway version for dispatch.")
        parser.add_argument("--extension-slug", type=str, default="", help="Extension slug for extension actions.")
        parser.add_argument("--agent-slug", type=str, default="", help="External agent slug.")
        parser.add_argument("--agent-name", type=str, default="", help="External agent name for registration.")
        parser.add_argument("--agent-endpoint", type=str, default="", help="External agent endpoint for registration.")
        parser.add_argument("--operation", type=str, default="", help="External agent operation for run.")
        parser.add_argument("--sync-type", type=str, default="delta", help="Cross sync type.")
        parser.add_argument("--target-platform", type=str, default="", help="Cross sync target platform.")

    def handle(self, *args, **options):
        action = options["action"]

        if action == "compile":
            result = self._handle_compile(options)
        elif action == "batch-compile":
            result = self._handle_batch_compile(options)
        elif action == "diff":
            result = self._handle_diff(options)
        elif action == "export":
            result = self._handle_export(options)
        elif action == "pipeline-run":
            result = self._handle_pipeline_run(options)
        elif action == "schedule-run":
            result = self._handle_schedule_run(options)
        elif action == "version-commit":
            result = self._handle_version_commit(options)
        elif action == "version-checkout":
            result = self._handle_version_checkout(options)
        elif action == "merge":
            result = self._handle_merge(options)
        elif action == "marketplace-install":
            result = self._handle_marketplace_install(options)
        elif action == "gateway-introspect":
            result = self._handle_gateway_introspect(options)
        elif action == "gateway-dispatch":
            result = self._handle_gateway_dispatch(options)
        elif action == "btif-export":
            result = self._handle_btif_export(options)
        elif action == "btif-validate":
            result = self._handle_btif_validate(options)
        elif action == "extension-apply":
            result = self._handle_extension_apply(options)
        elif action == "extension-rollback":
            result = self._handle_extension_rollback(options)
        elif action == "external-agent-register":
            result = self._handle_external_agent_register(options)
        elif action == "external-agent-run":
            result = self._handle_external_agent_run(options)
        elif action == "cross-sync-run":
            result = self._handle_cross_sync_run(options)
        else:
            raise CommandError(f"Unsupported action: {action}")

        self.stdout.write(json.dumps(result, sort_keys=True))

    def _parse_json(self, raw: str, *, field_name: str) -> object:
        text = (raw or "").strip()
        if not text:
            raise CommandError(f"{field_name} is required.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON for {field_name}: {exc}") from exc

    def _resolve_actor(self, options: dict[str, object]):
        return resolve_actor_by_username(str(options.get("actor_username", "") or ""))

    def _ensure_capability(self, options: dict[str, object], capability: str, *, project: ProjectNode | None = None):
        actor = self._resolve_actor(options)
        if actor and not has_semantic_capability(actor, capability, project=project):
            raise CommandError(f"User '{actor.username}' lacks capability '{capability}'.")
        return actor

    def _audit(self, *, options: dict[str, object], action: str, project: ProjectNode | None = None, payload: dict[str, object] | None = None):
        actor = self._resolve_actor(options)
        record_semantic_audit_log(
            actor=actor,
            action=action,
            project=project,
            payload=payload or {},
            source="cli",
        )

    def _validate_compile_payload(self, payload: dict[str, object]) -> dict[str, object]:
        serializer = ProjectNodeWriteSerializer(data=payload)
        if not serializer.is_valid():
            raise CommandError(json.dumps(serializer.errors, sort_keys=True))
        return serializer.validated_data

    def _handle_compile(self, options: dict[str, object]) -> dict[str, object]:
        payload = self._parse_json(options.get("payload_json", ""), field_name="--payload-json")
        if not isinstance(payload, dict):
            raise CommandError("--payload-json must be a JSON object for compile.")

        self._ensure_capability(options, "compile.semantic")
        validated = self._validate_compile_payload(payload)
        compiled, node = compile_and_store_project_node(validated)
        self._audit(
            options=options,
            action="compile.semantic",
            project=node,
            payload={"slug": node.slug, "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", "")},
        )

        return {
            "action": "compile",
            "project": {
                "id": node.id,
                "slug": node.slug,
                "name": node.name,
            },
            "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", ""),
            "alert_count": len(compiled.get("semantic_alerts", [])),
        }

    def _handle_batch_compile(self, options: dict[str, object]) -> dict[str, object]:
        payload = self._parse_json(options.get("payload_json", ""), field_name="--payload-json")
        self._ensure_capability(options, "compile.semantic")

        if isinstance(payload, dict):
            projects = payload.get("projects", [])
            atomic_mode = bool(options.get("atomic", False) or payload.get("atomic", False))
        elif isinstance(payload, list):
            projects = payload
            atomic_mode = bool(options.get("atomic", False))
        else:
            raise CommandError("--payload-json must be a JSON array or object with projects for batch-compile.")

        if not isinstance(projects, list) or not projects:
            raise CommandError("Batch payload requires a non-empty projects list.")

        results: list[dict[str, object]] = []
        compiled_count = 0
        failed_count = 0

        def process_item(index: int, item: object) -> None:
            nonlocal compiled_count, failed_count
            if not isinstance(item, dict):
                failed_count += 1
                results.append({"index": index, "status": "failed", "errors": {"payload": "Item must be an object."}})
                if atomic_mode:
                    raise CommandError(f"Atomic batch failed at index {index}: payload must be an object.")
                return

            serializer = ProjectNodeWriteSerializer(data=item)
            if not serializer.is_valid():
                failed_count += 1
                results.append({"index": index, "status": "failed", "errors": serializer.errors})
                if atomic_mode:
                    raise CommandError(f"Atomic batch failed at index {index}: {json.dumps(serializer.errors, sort_keys=True)}")
                return

            compiled_payload, node = compile_and_store_project_node(serializer.validated_data)
            compiled_count += 1
            results.append(
                {
                    "index": index,
                    "status": "compiled",
                    "slug": node.slug,
                    "identity_uri": compiled_payload.get("identity_payload", {}).get("identity", {}).get("identity_uri", ""),
                }
            )

        if atomic_mode:
            with transaction.atomic():
                for index, item in enumerate(projects):
                    process_item(index, item)
        else:
            for index, item in enumerate(projects):
                process_item(index, item)

        result = {
            "action": "batch-compile",
            "atomic": atomic_mode,
            "summary": {
                "requested": len(projects),
                "compiled": compiled_count,
                "failed": failed_count,
            },
            "results": results,
        }
        self._audit(options=options, action="batch.compile.semantic", payload=result.get("summary", {}))
        return result

    def _handle_diff(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "diff.semantic")
        source = self._parse_json(options.get("source_json", ""), field_name="--source-json")
        target = self._parse_json(options.get("target_json", ""), field_name="--target-json")

        if not isinstance(source, dict) or not isinstance(target, dict):
            raise CommandError("--source-json and --target-json must be JSON objects.")

        result = {
            "action": "diff",
            "diff": build_semantic_diff(source, target),
        }
        self._audit(options=options, action="diff.semantic", payload={"has_changes": bool(result.get("diff", {}).get("has_changes", False))})
        return result

    def _handle_export(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "export.semantic")
        scope = options.get("scope", "all")
        project_slug = (options.get("project_slug", "") or "").strip() or None
        if scope == "project" and not project_slug:
            raise CommandError("--project-slug is required when --scope=project.")

        payload = build_semantic_export_payload(
            scope=scope,
            project_slug=project_slug,
            include_history=bool(options.get("include_history", False)),
            max_items=int(options.get("max_items", 100) or 100),
            exported_by=str(options.get("triggered_by", "cli") or "cli"),
        )
        result = {
            "action": "export",
            "summary": payload.get("summary", {}),
            "filter": payload.get("filter", {}),
        }
        self._audit(options=options, action="export.semantic", payload={"scope": scope, "project_count": payload.get("summary", {}).get("project_count", 0)})
        return result

    def _handle_pipeline_run(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "run.pipeline")
        pipeline_slug = (options.get("pipeline_slug", "") or "").strip()
        if not pipeline_slug:
            raise CommandError("--pipeline-slug is required for pipeline-run.")

        pipeline = SemanticPipeline.objects.filter(slug=pipeline_slug, is_active=True).first()
        if not pipeline:
            raise CommandError("Active semantic pipeline not found.")

        run = run_semantic_pipeline(pipeline, triggered_by=str(options.get("triggered_by", "cli") or "cli"))
        result = {
            "action": "pipeline-run",
            "pipeline": pipeline.slug,
            "run_id": run.id,
            "status": run.status,
            "error_message": run.error_message,
        }
        self._audit(options=options, action="pipeline.run", payload={"pipeline_slug": pipeline.slug, "status": run.status})
        return result

    def _handle_schedule_run(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "run.schedule")
        schedule_slug = (options.get("schedule_slug", "") or "").strip()
        if not schedule_slug:
            raise CommandError("--schedule-slug is required for schedule-run.")

        schedule = SemanticSchedule.objects.filter(slug=schedule_slug).first()
        if not schedule:
            raise CommandError("Semantic schedule not found.")

        run = run_semantic_schedule(schedule, triggered_by=str(options.get("triggered_by", "cli") or "cli"))
        result = {
            "action": "schedule-run",
            "schedule": schedule.slug,
            "run_id": run.id,
            "status": run.status,
            "error_message": run.error_message,
        }
        self._audit(options=options, action="schedule.run", payload={"schedule_slug": schedule.slug, "status": run.status})
        return result

    def _handle_version_commit(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "version.commit")
        project_slug = (options.get("project_slug", "") or "").strip()
        if not project_slug:
            raise CommandError("--project-slug is required for version-commit.")

        project = ProjectNode.objects.filter(slug=project_slug).first()
        if not project:
            raise CommandError("Project not found.")

        actor = self._resolve_actor(options)
        version = commit_semantic_version(project=project, author=actor, message=str(options.get("message", "") or ""))
        result = {
            "action": "version-commit",
            "project": project.slug,
            "version_id": version.id,
            "version_number": version.version_number,
        }
        self._audit(options=options, action="version.commit", project=project, payload={"version_id": version.id, "version_number": version.version_number})
        return result

    def _handle_version_checkout(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "version.checkout")
        version_id = int(options.get("version_id", 0) or 0)
        if version_id <= 0:
            raise CommandError("--version-id is required for version-checkout.")

        version = SemanticVersion.objects.select_related("project").filter(id=version_id).first()
        if not version:
            raise CommandError("Version not found.")

        actor = self._resolve_actor(options)
        project = checkout_semantic_version(version=version, actor=actor)
        result = {
            "action": "version-checkout",
            "project": project.slug,
            "version_id": version.id,
            "version_number": version.version_number,
        }
        self._audit(options=options, action="version.checkout", project=project, payload={"version_id": version.id, "version_number": version.version_number})
        return result

    def _handle_merge(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "merge.semantic")
        left = self._parse_json(options.get("source_json", ""), field_name="--source-json")
        right = self._parse_json(options.get("target_json", ""), field_name="--target-json")
        base_text = (options.get("payload_json", "") or "").strip()
        base = self._parse_json(base_text, field_name="--payload-json") if base_text else {}

        if not isinstance(left, dict) or not isinstance(right, dict) or not isinstance(base, dict):
            raise CommandError("--source-json, --target-json and optional --payload-json must be JSON objects.")

        merge_result = merge_semantic_states(left, right, base=base)
        result = {
            "action": "merge",
            "result": merge_result,
        }
        self._audit(options=options, action="merge.semantic", payload={"has_conflicts": bool(merge_result.get("has_conflicts", False))})
        return result

    def _handle_marketplace_install(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "manage.marketplace")
        item_slug = (options.get("item_slug", "") or "").strip()
        if not item_slug:
            raise CommandError("--item-slug is required for marketplace-install.")
        actor = self._resolve_actor(options)
        result = install_marketplace_item(
            item_slug=item_slug,
            requested_version=(options.get("requested_version", "") or "").strip() or None,
            owner=actor,
        )
        self._audit(options=options, action="marketplace.install", payload=result)
        return {"action": "marketplace-install", **result}

    def _handle_gateway_introspect(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "gateway.inspect")
        result = {
            "action": "gateway-introspect",
            "route_map": gateway_route_map(),
            "schema": gateway_schema_introspection(),
            "health": gateway_health_status(),
        }
        self._audit(options=options, action="gateway.inspect", payload={"status": result["health"].get("status")})
        return result

    def _handle_gateway_dispatch(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "gateway.dispatch")
        route = (options.get("route", "") or "").strip()
        if not route:
            raise CommandError("--route is required for gateway-dispatch.")
        result = gateway_dispatch(route=route, requested_version=(options.get("gateway_version", "") or "").strip() or None)
        self._audit(options=options, action="gateway.dispatch", payload=result)
        return {"action": "gateway-dispatch", **result}

    def _handle_btif_export(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "btif.interop")
        project_slug = (options.get("project_slug", "") or "").strip()
        if not project_slug:
            raise CommandError("--project-slug is required for btif-export.")
        payload = encode_btif_plus(project_slug=project_slug)
        validation = validate_btif_plus(payload)
        self._audit(options=options, action="btif.export", payload={"project_slug": project_slug, "valid": validation.get("valid", False)})
        return {"action": "btif-export", "payload": payload, "validation": validation}

    def _handle_btif_validate(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "btif.interop")
        payload = self._parse_json(options.get("payload_json", ""), field_name="--payload-json")
        if not isinstance(payload, dict):
            raise CommandError("--payload-json must be a JSON object for btif-validate.")
        decoded = decode_btif_plus(payload)
        validation = validate_btif_plus(decoded)
        self._audit(options=options, action="btif.validate", payload={"valid": validation.get("valid", False)})
        return {"action": "btif-validate", "validation": validation}

    def _handle_extension_apply(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "manage.extensions")
        extension_slug = (options.get("extension_slug", "") or "").strip()
        if not extension_slug:
            raise CommandError("--extension-slug is required for extension-apply.")
        result = apply_semantic_extension(extension_slug=extension_slug)
        self._audit(options=options, action="extension.apply", payload=result)
        return {"action": "extension-apply", **result}

    def _handle_extension_rollback(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "manage.extensions")
        extension_slug = (options.get("extension_slug", "") or "").strip()
        if not extension_slug:
            raise CommandError("--extension-slug is required for extension-rollback.")
        result = rollback_semantic_extension(extension_slug=extension_slug)
        self._audit(options=options, action="extension.rollback", payload=result)
        return {"action": "extension-rollback", **result}

    def _handle_external_agent_register(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "manage.external_agents")
        slug = (options.get("agent_slug", "") or "").strip()
        name = (options.get("agent_name", "") or "").strip()
        endpoint = (options.get("agent_endpoint", "") or "").strip()
        if not slug or not endpoint:
            raise CommandError("--agent-slug and --agent-endpoint are required for external-agent-register.")
        agent = register_external_agent(
            {
                "slug": slug,
                "name": name or slug,
                "endpoint": endpoint,
            }
        )
        result = {"agent_slug": agent.slug, "status": agent.status}
        self._audit(options=options, action="external.agent.register", payload=result)
        return {"action": "external-agent-register", **result}

    def _handle_external_agent_run(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "manage.external_agents")
        slug = (options.get("agent_slug", "") or "").strip()
        operation = (options.get("operation", "") or "").strip()
        if not slug or not operation:
            raise CommandError("--agent-slug and --operation are required for external-agent-run.")
        payload = self._parse_json(options.get("payload_json", "{}") or "{}", field_name="--payload-json")
        if not isinstance(payload, dict):
            raise CommandError("--payload-json must be a JSON object for external-agent-run.")
        result = run_external_agent(agent_slug=slug, operation=operation, payload=payload)
        self._audit(options=options, action="external.agent.run", payload={"agent_slug": result.get("agent_slug"), "status": result.get("status")})
        return {"action": "external-agent-run", **result}

    def _handle_cross_sync_run(self, options: dict[str, object]) -> dict[str, object]:
        self._ensure_capability(options, "sync.cross_platform")
        project_slug = (options.get("project_slug", "") or "").strip()
        target_platform = (options.get("target_platform", "") or "").strip()
        if not project_slug or not target_platform:
            raise CommandError("--project-slug and --target-platform are required for cross-sync-run.")
        result = run_semantic_cross_sync(
            sync_type=(options.get("sync_type", "delta") or "delta").strip(),
            target_platform=target_platform,
            project_slug=project_slug,
        )
        self._audit(options=options, action="sync.cross_platform", payload=result)
        return {"action": "cross-sync-run", **result}
