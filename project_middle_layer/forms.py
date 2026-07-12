from django import forms
import json

from .models import ProjectNode, SemanticPipeline, SemanticRole


class ProjectMiddleLayerCompileForm(forms.Form):
    title = forms.CharField(max_length=255, label="Project Title")
    intent = forms.CharField(max_length=120, label="Semantic Intent")
    tier = forms.CharField(max_length=120, label="Visibility Tier", initial="public")
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    tags = forms.CharField(
        label="Semantic Tags",
        help_text="Comma-separated tags like storytelling, community, workshops, local-media.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def clean_title(self):
        return self.cleaned_data["title"].strip()

    def clean_intent(self):
        return self.cleaned_data["intent"].strip()

    def clean_tier(self):
        return self.cleaned_data["tier"].strip()

    def clean_tags(self):
        raw_tags = self.cleaned_data["tags"]
        normalized = sorted(
            {
                tag.strip().lower()
                for tag in raw_tags.replace("\n", ",").split(",")
                if tag.strip()
            }
        )
        if not normalized:
            raise forms.ValidationError("At least one semantic tag is required.")
        return normalized


class ProjectMiddleLayerBatchCompileForm(forms.Form):
    payload_json = forms.CharField(
        label="Batch Payload JSON",
        help_text="Provide a JSON array of project payloads or an object with a 'projects' array.",
        widget=forms.Textarea(attrs={"rows": 16}),
    )
    atomic = forms.BooleanField(required=False, initial=False, label="Atomic Mode")

    def clean_payload_json(self):
        raw = self.cleaned_data["payload_json"].strip()
        if not raw:
            raise forms.ValidationError("Batch payload JSON is required.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc

        if isinstance(parsed, dict):
            projects = parsed.get("projects")
            if not isinstance(projects, list):
                raise forms.ValidationError("JSON object payload must contain a 'projects' array.")
            parsed = projects

        if not isinstance(parsed, list):
            raise forms.ValidationError("Batch payload must be a JSON array or an object with 'projects'.")
        if not parsed:
            raise forms.ValidationError("Batch payload must contain at least one project.")

        return parsed


class ProjectMiddleLayerExportForm(forms.Form):
    scope = forms.ChoiceField(
        choices=[("all", "All Projects"), ("project", "Single Project")],
        initial="all",
        label="Export Scope",
    )
    project_slug = forms.SlugField(required=False, max_length=120, label="Project Slug")
    include_history = forms.BooleanField(required=False, initial=False, label="Include Full History")
    download = forms.BooleanField(required=False, initial=True, label="Download as JSON")
    max_items = forms.IntegerField(required=False, min_value=1, max_value=500, initial=100, label="Max Projects")

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope", "all")
        project_slug = (cleaned.get("project_slug") or "").strip()

        if scope == "project":
            if not project_slug:
                self.add_error("project_slug", "Project slug is required when exporting a single project.")
            elif not ProjectNode.objects.filter(slug=project_slug).exists():
                self.add_error("project_slug", "Project slug not found.")
        cleaned["project_slug"] = project_slug or None
        return cleaned


class ProjectMiddleLayerPipelineForm(forms.Form):
    name = forms.CharField(max_length=120, label="Pipeline Name")
    slug = forms.SlugField(max_length=120, label="Pipeline Slug")
    steps_json = forms.CharField(
        label="Pipeline Steps JSON",
        help_text="JSON array of step objects, e.g. [{\"action\":\"compile\",\"payload\":{...}}].",
        widget=forms.Textarea(attrs={"rows": 12}),
    )
    triggers_json = forms.CharField(
        required=False,
        label="Triggers JSON",
        help_text="Optional JSON object like {\"mode\":\"manual\"} or schedule metadata.",
        widget=forms.Textarea(attrs={"rows": 4}),
        initial='{"mode": "manual"}',
    )
    is_active = forms.BooleanField(required=False, initial=True, label="Active")

    def clean_steps_json(self):
        raw = self.cleaned_data["steps_json"].strip()
        if not raw:
            raise forms.ValidationError("Pipeline steps JSON is required.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid steps JSON: {exc}") from exc

        if not isinstance(parsed, list) or not parsed:
            raise forms.ValidationError("Pipeline steps must be a non-empty JSON array.")

        for index, step in enumerate(parsed):
            if not isinstance(step, dict):
                raise forms.ValidationError(f"Step {index} must be a JSON object.")
            action = str(step.get("action") or "").strip().lower()
            if not action:
                raise forms.ValidationError(f"Step {index} requires an action.")

        return parsed

    def clean_triggers_json(self):
        raw = (self.cleaned_data.get("triggers_json") or "").strip()
        if not raw:
            return {"mode": "manual"}

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid triggers JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise forms.ValidationError("Triggers must be a JSON object.")
        return parsed


class ProjectMiddleLayerScheduleForm(forms.Form):
    name = forms.CharField(max_length=120, label="Schedule Name")
    slug = forms.SlugField(max_length=120, label="Schedule Slug")
    cron_expression = forms.CharField(max_length=64, label="Cron Expression", initial="0 0 * * *")
    action = forms.ChoiceField(
        choices=[("pipeline-run", "Pipeline Run"), ("export", "Export"), ("alert-check", "Alert Check")],
        label="Action",
    )
    pipeline_slug = forms.SlugField(required=False, max_length=120, label="Pipeline Slug")
    payload_json = forms.CharField(
        required=False,
        label="Payload JSON",
        help_text="Optional JSON object used by schedule action.",
        widget=forms.Textarea(attrs={"rows": 6}),
        initial="{}",
    )
    is_paused = forms.BooleanField(required=False, initial=False, label="Paused")

    def clean_payload_json(self):
        raw = (self.cleaned_data.get("payload_json") or "").strip()
        if not raw:
            return {}

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid payload JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise forms.ValidationError("Payload JSON must be an object.")
        return parsed

    def clean(self):
        cleaned = super().clean()
        action = cleaned.get("action")
        pipeline_slug = (cleaned.get("pipeline_slug") or "").strip()

        if action == "pipeline-run":
            if not pipeline_slug:
                self.add_error("pipeline_slug", "Pipeline slug is required for pipeline-run action.")
            elif not SemanticPipeline.objects.filter(slug=pipeline_slug).exists():
                self.add_error("pipeline_slug", "Pipeline slug not found.")

        cleaned["pipeline_slug"] = pipeline_slug or None
        return cleaned


class ProjectMiddleLayerWebhookForm(forms.Form):
    name = forms.CharField(max_length=120, label="Webhook Name")
    target_url = forms.URLField(max_length=500, label="Target URL")
    event_type = forms.CharField(max_length=64, label="Event Type")
    secret_token = forms.CharField(required=False, max_length=255, label="Secret Token")
    status = forms.ChoiceField(
        choices=[("active", "Active"), ("disabled", "Disabled")],
        initial="active",
        label="Status",
    )

    def clean_event_type(self):
        return self.cleaned_data["event_type"].strip().lower()


class ProjectMiddleLayerIntegrationForm(forms.Form):
    name = forms.CharField(max_length=120, label="Integration Name")
    slug = forms.SlugField(max_length=120, label="Integration Slug")
    direction = forms.ChoiceField(
        choices=[("inbound", "Inbound"), ("outbound", "Outbound"), ("bidirectional", "Bidirectional")],
        label="Direction",
    )
    target_system = forms.CharField(max_length=120, label="Target System")
    endpoint_url = forms.URLField(max_length=500, required=False, label="Endpoint URL")
    api_key = forms.CharField(max_length=64, label="API Key")
    permissions_csv = forms.CharField(
        required=False,
        label="Permissions",
        help_text="Comma-separated permissions like inbound.sync, outbound.export.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    status = forms.ChoiceField(
        choices=[("active", "Active"), ("disabled", "Disabled")],
        initial="active",
        label="Status",
    )

    def clean_permissions_csv(self):
        raw = self.cleaned_data.get("permissions_csv") or ""
        return sorted({item.strip().lower() for item in raw.replace("\n", ",").split(",") if item.strip()})


class ProjectMiddleLayerSearchForm(forms.Form):
    q = forms.CharField(max_length=255, required=False, label="Query")
    limit = forms.IntegerField(required=False, min_value=1, max_value=200, initial=50, label="Limit")

    def clean_q(self):
        return (self.cleaned_data.get("q") or "").strip()


class ProjectMiddleLayerAgentRunForm(forms.Form):
    agent_name = forms.ChoiceField(
        choices=[
            ("Drift Agent", "Drift Agent"),
            ("Stability Agent", "Stability Agent"),
            ("Lineage Agent", "Lineage Agent"),
            ("Tag Agent", "Tag Agent"),
            ("Evolution Agent", "Evolution Agent"),
        ],
        label="Agent",
    )


class ProjectMiddleLayerAnalyticsForm(forms.Form):
    branch_filter = forms.CharField(max_length=120, required=False, label="Branch Filter")
    tier_filter = forms.CharField(max_length=120, required=False, label="Tier Filter")
    limit = forms.IntegerField(required=False, min_value=1, max_value=100, initial=30, label="Trend Limit")

    def clean_branch_filter(self):
        return (self.cleaned_data.get("branch_filter") or "").strip()

    def clean_tier_filter(self):
        return (self.cleaned_data.get("tier_filter") or "").strip()


class SemanticRoleForm(forms.Form):
    name = forms.CharField(max_length=120, label="Role Name")
    slug = forms.SlugField(max_length=120, label="Role Slug")
    capabilities_csv = forms.CharField(
        required=False,
        label="Capabilities",
        help_text="Comma-separated capabilities such as view.semantic, compile.semantic, run.pipeline, manage.schedule.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_capabilities_csv(self):
        raw = self.cleaned_data.get("capabilities_csv") or ""
        return sorted({item.strip().lower() for item in raw.replace("\n", ",").split(",") if item.strip()})


class SemanticPermissionForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    role_slug = forms.SlugField(max_length=120, label="Role Slug")
    project_slug = forms.SlugField(required=False, max_length=120, label="Project Slug")
    tier = forms.CharField(required=False, max_length=120, label="Tier")
    branch = forms.CharField(required=False, max_length=120, label="Branch")

    def clean_role_slug(self):
        slug = (self.cleaned_data.get("role_slug") or "").strip()
        if not SemanticRole.objects.filter(slug=slug).exists():
            raise forms.ValidationError("Role slug not found.")
        return slug


class SemanticEditSessionForm(forms.Form):
    project_slug = forms.SlugField(max_length=120, label="Project Slug")
    force_takeover = forms.BooleanField(required=False, initial=False, label="Force Takeover")


class SemanticChangeRequestForm(forms.Form):
    project_slug = forms.SlugField(max_length=120, label="Project Slug")
    proposed_changes_json = forms.CharField(
        label="Proposed Changes JSON",
        widget=forms.Textarea(attrs={"rows": 10}),
    )

    def clean_proposed_changes_json(self):
        raw = (self.cleaned_data.get("proposed_changes_json") or "").strip()
        if not raw:
            raise forms.ValidationError("Proposed changes JSON is required.")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("Proposed changes must be a JSON object.")
        return parsed


class SemanticChangeReviewForm(forms.Form):
    change_request_id = forms.IntegerField(min_value=1, label="Change Request ID")
    approve = forms.BooleanField(required=False, label="Approve")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Review Notes")


class SemanticAuditFilterForm(forms.Form):
    actor_username = forms.CharField(required=False, max_length=150, label="Actor Username")
    action = forms.CharField(required=False, max_length=120, label="Action")
    project_slug = forms.SlugField(required=False, max_length=120, label="Project Slug")
    source = forms.CharField(required=False, max_length=50, label="Source")


class SemanticVersionCommitForm(forms.Form):
    project_slug = forms.SlugField(max_length=120, label="Project Slug")
    message = forms.CharField(required=False, max_length=255, label="Message")


class SemanticVersionCheckoutForm(forms.Form):
    version_id = forms.IntegerField(min_value=1, label="Version ID")


class ReplicationConfigForm(forms.Form):
    name = forms.CharField(max_length=120, label="Name")
    slug = forms.SlugField(max_length=120, label="Slug")
    remote_node_url = forms.URLField(max_length=500, label="Remote Node URL")
    api_key = forms.CharField(max_length=128, label="API Key")
    mode = forms.ChoiceField(
        choices=[
            ("full", "Full Replication"),
            ("branch_only", "Branch Only"),
            ("tier_only", "Tier Only"),
            ("snapshot_only", "Snapshot Only"),
        ],
        initial="full",
        label="Replication Mode",
    )
    direction = forms.ChoiceField(
        choices=[("push", "Push"), ("pull", "Pull"), ("bidirectional", "Bidirectional")],
        initial="bidirectional",
        label="Direction",
    )
    is_active = forms.BooleanField(required=False, initial=True, label="Active")


class FederationPeerForm(forms.Form):
    name = forms.CharField(max_length=120, label="Name")
    slug = forms.SlugField(max_length=120, label="Slug")
    peer_identity = forms.CharField(max_length=255, label="Peer Identity")
    peer_url = forms.URLField(max_length=500, label="Peer URL")
    capabilities_csv = forms.CharField(
        required=False,
        label="Capabilities",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Comma-separated capabilities shared by this peer.",
    )
    sync_rules_json = forms.CharField(
        required=False,
        label="Sync Rules JSON",
        widget=forms.Textarea(attrs={"rows": 4}),
        initial="{}",
    )
    is_active = forms.BooleanField(required=False, initial=True, label="Active")

    def clean_capabilities_csv(self):
        raw = self.cleaned_data.get("capabilities_csv") or ""
        return sorted({item.strip().lower() for item in raw.replace("\n", ",").split(",") if item.strip()})

    def clean_sync_rules_json(self):
        raw = (self.cleaned_data.get("sync_rules_json") or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("Sync rules must be a JSON object.")
        return parsed


class SemanticShardForm(forms.Form):
    name = forms.CharField(max_length=120, label="Name")
    slug = forms.SlugField(max_length=120, label="Slug")
    node_url = forms.URLField(max_length=500, required=False, label="Node URL")
    strategy = forms.ChoiceField(
        choices=[
            ("branch", "By Branch"),
            ("tier", "By Tier"),
            ("slug_prefix", "By Project Slug Prefix"),
            ("cluster", "By Semantic Cluster"),
        ],
        initial="branch",
        label="Strategy",
    )
    route_value = forms.CharField(required=False, max_length=120, label="Route Value")
    is_active = forms.BooleanField(required=False, initial=True, label="Active")


class SemanticCacheControlForm(forms.Form):
    target = forms.ChoiceField(
        choices=[
            ("analytics", "Analytics"),
            ("search", "Search"),
            ("insights", "Insights"),
            ("diff", "Diff"),
        ],
        initial="analytics",
        label="Cache Target",
    )
    params_json = forms.CharField(
        required=False,
        label="Params JSON",
        widget=forms.Textarea(attrs={"rows": 4}),
        initial="{}",
    )

    def clean_params_json(self):
        raw = (self.cleaned_data.get("params_json") or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("Params must be a JSON object.")
        return parsed


class SemanticSyncForm(forms.Form):
    sync_type = forms.ChoiceField(
        choices=[
            ("version", "Version Sync"),
            ("snapshot", "Snapshot Sync"),
            ("lineage", "Lineage Sync"),
            ("tag", "Tag Sync"),
            ("alert", "Alert/Recommendation Sync"),
        ],
        initial="version",
        label="Sync Type",
    )
    target_slug = forms.SlugField(required=False, max_length=120, label="Target Replication Slug")


class DistributedAgentRunForm(forms.Form):
    agent_name = forms.ChoiceField(
        choices=[
            ("Global Drift Agent", "Global Drift Agent"),
            ("Global Stability Agent", "Global Stability Agent"),
            ("Federated Lineage Agent", "Federated Lineage Agent"),
            ("Shard Health Agent", "Shard Health Agent"),
        ],
        label="Distributed Agent",
    )


class MarketplaceInstallForm(forms.Form):
    item_slug = forms.SlugField(max_length=120, label="Marketplace Item Slug")
    requested_version = forms.CharField(required=False, max_length=40, label="Requested Version")


class SemanticPluginForm(forms.Form):
    name = forms.CharField(max_length=120, label="Plugin Name")
    slug = forms.SlugField(max_length=120, label="Plugin Slug")
    plugin_type = forms.CharField(max_length=40, initial="agent", label="Plugin Type")
    entrypoint = forms.CharField(max_length=255, label="Entrypoint")
    capabilities_csv = forms.CharField(
        required=False,
        label="Capabilities",
        help_text="Comma-separated capability keys.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    version = forms.CharField(required=False, max_length=40, initial="0.0.1", label="Version")
    enabled = forms.BooleanField(required=False, initial=False, label="Enabled")

    def clean_capabilities_csv(self):
        raw = self.cleaned_data.get("capabilities_csv") or ""
        return sorted({item.strip().lower() for item in raw.replace("\n", ",").split(",") if item.strip()})


class SemanticExtensionForm(forms.Form):
    name = forms.CharField(max_length=120, label="Extension Name")
    slug = forms.SlugField(max_length=120, label="Extension Slug")
    version = forms.CharField(required=False, max_length=40, initial="0.0.1", label="Version")
    schema_patch_json = forms.CharField(
        required=False,
        label="Schema Patch JSON",
        widget=forms.Textarea(attrs={"rows": 6}),
        initial="{}",
    )
    rules_patch_json = forms.CharField(
        required=False,
        label="Rules Patch JSON",
        widget=forms.Textarea(attrs={"rows": 6}),
        initial="{}",
    )

    def _parse_json_object(self, key: str, label: str):
        raw = (self.cleaned_data.get(key) or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid {label}: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError(f"{label} must be a JSON object.")
        return parsed

    def clean_schema_patch_json(self):
        return self._parse_json_object("schema_patch_json", "schema patch JSON")

    def clean_rules_patch_json(self):
        return self._parse_json_object("rules_patch_json", "rules patch JSON")


class SemanticGatewayForm(forms.Form):
    requested_version = forms.CharField(required=False, max_length=20, initial="v1", label="Gateway Version")
    route = forms.CharField(required=False, max_length=120, label="Route")


class BtifPlusForm(forms.Form):
    project_slug = forms.SlugField(max_length=120, label="Project Slug")
    payload_json = forms.CharField(
        required=False,
        label="BTIF+ Payload JSON",
        widget=forms.Textarea(attrs={"rows": 8}),
    )

    def clean_payload_json(self):
        raw = (self.cleaned_data.get("payload_json") or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid BTIF+ payload JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("BTIF+ payload JSON must be an object.")
        return parsed


class ExternalAgentForm(forms.Form):
    name = forms.CharField(max_length=120, label="Agent Name")
    slug = forms.SlugField(max_length=120, label="Agent Slug")
    endpoint = forms.URLField(max_length=500, label="Endpoint")
    capabilities_csv = forms.CharField(
        required=False,
        label="Capabilities",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    auth_token = forms.CharField(required=False, max_length=255, label="Auth Token")
    status = forms.ChoiceField(
        choices=[("active", "Active"), ("disabled", "Disabled")],
        initial="active",
        label="Status",
    )

    def clean_capabilities_csv(self):
        raw = self.cleaned_data.get("capabilities_csv") or ""
        return sorted({item.strip().lower() for item in raw.replace("\n", ",").split(",") if item.strip()})


class SemanticCrossSyncForm(forms.Form):
    sync_type = forms.ChoiceField(
        choices=[
            ("full", "Full Sync"),
            ("delta", "Delta Sync"),
            ("version", "Version Sync"),
            ("lineage", "Lineage Sync"),
            ("analytics", "Analytics Sync"),
            ("insight", "Insight Sync"),
        ],
        initial="delta",
        label="Cross Sync Type",
    )
    target_platform = forms.CharField(max_length=120, label="Target Platform")
    project_slug = forms.SlugField(max_length=120, label="Project Slug")
