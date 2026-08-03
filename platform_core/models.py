from django.conf import settings
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid


def _billing_access_link_key():
    return uuid.uuid4().hex


class InsightsDailySnapshot(models.Model):
    snapshot_date = models.DateField(unique=True)
    pressure_index = models.FloatField(default=0.0)
    average_health_score = models.FloatField(default=0.0)
    risk_flag_count = models.PositiveIntegerField(default=0)
    activity_count = models.PositiveIntegerField(default=0)
    user_growth_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-snapshot_date"]
        verbose_name = "Insights Daily Snapshot"
        verbose_name_plural = "Insights Daily Snapshots"

    def __str__(self):
        return f"Insights snapshot {self.snapshot_date.isoformat()}"


class InsightsNarrativeSnapshot(models.Model):
    snapshot_date = models.DateField(unique=True)
    state_label = models.CharField(max_length=32, default="Stable")
    pressure_index = models.FloatField(default=0.0)
    weighted_priority_score = models.FloatField(default=0.0)
    growth_direction = models.CharField(max_length=32, default="Mixed")
    quadrant_priority = models.CharField(max_length=16, default="Green")
    pipeline_bottleneck = models.CharField(max_length=120, default="N/A")
    recommended_action = models.TextField(blank=True, default="")
    daily_brief = models.TextField(blank=True, default="")
    weekly_summary = models.TextField(blank=True, default="")
    monthly_outlook = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-snapshot_date"]
        verbose_name = "Insights Narrative Snapshot"
        verbose_name_plural = "Insights Narrative Snapshots"

    def __str__(self):
        return f"Narrative snapshot {self.snapshot_date.isoformat()}"


class ClientContractProfile(models.Model):
    tenant_key = models.CharField(max_length=120, default="default")
    client_key = models.CharField(max_length=120)
    display_name = models.CharField(max_length=160, blank=True, default="")
    billing_contact_email = models.EmailField(blank=True, default="")
    billing_plan = models.CharField(max_length=32, blank=True, default="standard")
    monthly_event_allowance = models.PositiveIntegerField(default=1000)
    overage_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0.0100)
    default_schema_version = models.CharField(max_length=16, blank=True, default="")
    default_capabilities = models.TextField(blank=True, default="")
    strict_negotiation = models.BooleanField(default=False)
    strict_payload_shape = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client_key"]
        verbose_name = "Client Contract Profile"
        verbose_name_plural = "Client Contract Profiles"
        constraints = [
            models.UniqueConstraint(fields=["tenant_key", "client_key"], name="uniq_contract_profile_tenant_client"),
        ]

    def __str__(self):
        return self.display_name or f"{self.tenant_key}:{self.client_key}"


class ContractUsageEvent(models.Model):
    tenant_key = models.CharField(max_length=120, blank=True, default="default")
    client_key = models.CharField(max_length=120, blank=True, default="anonymous")
    endpoint = models.CharField(max_length=80)
    billable_category = models.CharField(max_length=32, blank=True, default="contract_api")
    billable_units = models.PositiveIntegerField(default=1)
    billable_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    requested_schema_version = models.CharField(max_length=32, blank=True, default="")
    selected_schema_version = models.CharField(max_length=32, blank=True, default="")
    negotiation_source = models.CharField(max_length=32, blank=True, default="")
    strict_negotiation = models.BooleanField(default=False)
    strict_payload_shape = models.BooleanField(default=False)
    period = models.CharField(max_length=24, blank=True, default="")
    output_format = models.CharField(max_length=24, blank=True, default="")
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Usage Event"
        verbose_name_plural = "Contract Usage Events"
        indexes = [
            models.Index(fields=["tenant_key", "created_at"]),
            models.Index(fields=["client_key", "created_at"]),
            models.Index(fields=["endpoint", "created_at"]),
            models.Index(fields=["status_code", "created_at"]),
        ]

    def __str__(self):
        return f"{self.endpoint} {self.tenant_key}:{self.client_key} {self.status_code}"


class QuadrantUsageEvent(models.Model):
    hour = models.PositiveSmallIntegerField()
    is_pm = models.BooleanField(default=False)
    slug = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quadrant Usage Event"
        verbose_name_plural = "Quadrant Usage Events"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["hour", "created_at"]),
            models.Index(fields=["slug", "created_at"]),
        ]

    def __str__(self):
        return f"quadrant {self.hour} {self.slug} {'PM' if self.is_pm else 'AM'}"


class ContractBillingSnapshot(models.Model):
    tenant_key = models.CharField(max_length=120, default="default")
    client_key = models.CharField(max_length=120, default="all")
    window_days = models.PositiveIntegerField(default=30)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    summary_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Billing Snapshot"
        verbose_name_plural = "Contract Billing Snapshots"
        indexes = [
            models.Index(fields=["tenant_key", "client_key", "created_at"]),
        ]

    def __str__(self):
        return f"{self.tenant_key}:{self.client_key} billing snapshot {self.created_at.isoformat()}"


class ContractBillingJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    JOB_BILLING_CYCLE = "billing_cycle"
    JOB_INVOICE_EXPORT = "invoice_export"
    JOB_NOTIFY = "notify"
    JOB_AUTOMATION = "automation"
    JOB_TYPE_CHOICES = [
        (JOB_BILLING_CYCLE, "Billing cycle"),
        (JOB_INVOICE_EXPORT, "Invoice export"),
        (JOB_NOTIFY, "Notify"),
        (JOB_AUTOMATION, "Operational automation"),
    ]

    tenant_key = models.CharField(max_length=120, default="default")
    client_key = models.CharField(max_length=120, default="all")
    job_type = models.CharField(max_length=32, choices=JOB_TYPE_CHOICES, default=JOB_BILLING_CYCLE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contract_billing_jobs",
    )
    payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Billing Job"
        verbose_name_plural = "Contract Billing Jobs"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["tenant_key", "client_key", "created_at"]),
        ]

    def __str__(self):
        return f"{self.job_type} {self.tenant_key}:{self.client_key} {self.status}"


class ContractBillingNotification(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_SENT = "sent"
    STATUS_SKIPPED = "skipped"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_SENT, "Sent"),
        (STATUS_SKIPPED, "Skipped"),
        (STATUS_FAILED, "Failed"),
    ]

    tenant_key = models.CharField(max_length=120, default="default")
    client_key = models.CharField(max_length=120, default="all")
    related_job = models.ForeignKey(
        ContractBillingJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    channel = models.CharField(max_length=24, default="email")
    recipient = models.EmailField(blank=True, default="")
    subject = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    retry_count = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Billing Notification"
        verbose_name_plural = "Contract Billing Notifications"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["tenant_key", "client_key", "created_at"]),
        ]

    def __str__(self):
        return f"{self.channel} {self.tenant_key}:{self.client_key} {self.status}"


class ContractBillingAccessLink(models.Model):
    link_key = models.CharField(max_length=32, unique=True, default=_billing_access_link_key)
    tenant_key = models.CharField(max_length=120, default="default")
    client_key = models.CharField(max_length=120, default="all")
    window_days = models.PositiveIntegerField(default=30)
    label = models.CharField(max_length=120, blank=True, default="")
    recipient_email = models.EmailField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contract_billing_access_links",
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contract Billing Access Link"
        verbose_name_plural = "Contract Billing Access Links"
        indexes = [
            models.Index(fields=["tenant_key", "client_key", "created_at"]),
            models.Index(fields=["is_active", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.tenant_key}:{self.client_key}:{self.link_key[:8]}"


class CustomerTenantMembership(models.Model):
    ROLE_VIEWER = "viewer"
    ROLE_BILLING = "billing"
    ROLE_OWNER = "owner"
    ROLE_CHOICES = [
        (ROLE_VIEWER, "Viewer"),
        (ROLE_BILLING, "Billing"),
        (ROLE_OWNER, "Owner"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_tenant_memberships",
    )
    tenant_key = models.CharField(max_length=120)
    client_key = models.CharField(max_length=120, default="all")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tenant_key", "client_key", "user_id"]
        verbose_name = "Customer Tenant Membership"
        verbose_name_plural = "Customer Tenant Memberships"
        constraints = [
            models.UniqueConstraint(fields=["user", "tenant_key", "client_key"], name="uniq_customer_tenant_membership"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.tenant_key}:{self.client_key}"


class SemanticPreset(models.Model):
    # Canonical name: phase.color.domain
    name = models.CharField(max_length=100, unique=True, db_index=True)

    # Raw metadata this preset injects
    phase = models.CharField(max_length=20, db_index=True)
    color_primary = models.CharField(max_length=20, db_index=True)
    metaphor = models.CharField(max_length=30, db_index=True)

    mlas_subject = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_branch = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_term = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_meta = models.CharField(max_length=30, blank=True, null=True, db_index=True)

    dewey_code = models.IntegerField(db_index=True)

    industry_super_sector = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    industry_sector = models.CharField(max_length=100, blank=True, null=True)
    industry_group = models.CharField(max_length=100, blank=True, null=True)
    industry_sub_industry = models.CharField(max_length=100, blank=True, null=True)

    ui_category = models.CharField(max_length=30, blank=True, null=True, db_index=True)

    # Preset metadata
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["phase"]),
            models.Index(fields=["color_primary"]),
            models.Index(fields=["mlas_subject", "mlas_branch", "mlas_term"]),
            models.Index(fields=["dewey_code"]),
        ]


class SemanticBundle(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    label = models.CharField(max_length=160)
    family = models.CharField(max_length=80, db_index=True)
    description = models.TextField(blank=True, default="")
    sequence = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="semantic_bundles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["family", "name"]),
        ]


class SemanticBundleRevision(models.Model):
    bundle = models.ForeignKey(
        SemanticBundle,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    revision_number = models.PositiveIntegerField()
    label = models.CharField(max_length=160)
    family = models.CharField(max_length=80, db_index=True)
    description = models.TextField(blank=True, default="")
    sequence = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="semantic_bundle_revisions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-revision_number", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["bundle", "revision_number"], name="platform_co_bundle_revision_unique"),
        ]
        indexes = [
            models.Index(fields=["bundle", "revision_number"]),
        ]


class SemanticBundleShare(models.Model):
    PERMISSION_VIEW = "view"
    PERMISSION_EDIT = "edit"
    PERMISSION_CHOICES = [
        (PERMISSION_VIEW, "View"),
        (PERMISSION_EDIT, "Edit"),
    ]

    bundle = models.ForeignKey(
        SemanticBundle,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="semantic_bundle_shares",
    )
    permission = models.CharField(max_length=12, choices=PERMISSION_CHOICES, default=PERMISSION_VIEW)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="semantic_bundle_shares_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["bundle", "user"], name="platform_co_bundle_share_unique"),
        ]
        indexes = [
            models.Index(fields=["bundle", "permission", "is_active"]),
        ]


class SemanticBundleRevisionTag(models.Model):
    bundle = models.ForeignKey(
        SemanticBundle,
        on_delete=models.CASCADE,
        related_name="revision_tags",
    )
    revision = models.ForeignKey(
        SemanticBundleRevision,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=64)
    note = models.CharField(max_length=240, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="semantic_bundle_revision_tags",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["bundle", "name"], name="platform_co_bundle_revision_tag_unique"),
        ]
        indexes = [
            models.Index(fields=["bundle", "name"]),
            models.Index(fields=["bundle", "revision"]),
        ]


class MLASClassificationRecord(models.Model):
    REVIEW_DRAFT = "draft"
    REVIEW_CANDIDATE = "candidate"
    REVIEW_APPROVED = "approved"
    REVIEW_REJECTED = "rejected"
    REVIEW_STATUS_CHOICES = [
        (REVIEW_DRAFT, "Draft"),
        (REVIEW_CANDIDATE, "Candidate"),
        (REVIEW_APPROVED, "Approved"),
        (REVIEW_REJECTED, "Rejected"),
    ]

    TARGET_TERM = "term"
    TARGET_META = "meta"
    TARGET_LAYER_CHOICES = [
        (TARGET_TERM, "Term (64)"),
        (TARGET_META, "MetaTerm (256)"),
    ]

    SCORE_VALIDATORS = [MinValueValidator(0.0), MaxValueValidator(1.0)]

    record_id = models.CharField(max_length=64, unique=True, db_index=True)
    source_name_raw = models.CharField(max_length=255)
    source_description_raw = models.TextField(blank=True, default="")

    target_layer = models.CharField(max_length=8, choices=TARGET_LAYER_CHOICES, default=TARGET_TERM)

    mlas_subject_code = models.CharField(max_length=16)
    mlas_branch_code = models.CharField(max_length=16, blank=True, default="")
    mlas_term_code = models.CharField(max_length=16, blank=True, default="")
    mlas_meta_term_code = models.CharField(max_length=16, blank=True, default="")

    dewey_code = models.CharField(max_length=32, blank=True, default="")
    gics_sector_code = models.CharField(max_length=32, blank=True, default="")
    gics_industry_group_code = models.CharField(max_length=32, blank=True, default="")
    gics_industry_code = models.CharField(max_length=32, blank=True, default="")
    gics_sub_industry_code = models.CharField(max_length=32, blank=True, default="")
    naics_code_2 = models.CharField(max_length=8, blank=True, default="")
    naics_code_3 = models.CharField(max_length=8, blank=True, default="")
    naics_code_4 = models.CharField(max_length=8, blank=True, default="")
    naics_code_5 = models.CharField(max_length=8, blank=True, default="")
    naics_code_6 = models.CharField(max_length=8, blank=True, default="")

    algorithm_1_score = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)
    algorithm_2_score = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)
    algorithm_3_score = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)
    algorithm_4_score = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)
    algorithm_consensus_score = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)

    quadrant_slug = models.CharField(max_length=64, blank=True, default="")
    basetrue_label = models.CharField(max_length=160, blank=True, default="")
    basetrue_description = models.TextField(blank=True, default="")

    confidence_overall = models.FloatField(validators=SCORE_VALIDATORS, default=0.0)
    confidence_reason = models.TextField(blank=True, default="")

    review_status = models.CharField(max_length=16, choices=REVIEW_STATUS_CHOICES, default=REVIEW_DRAFT, db_index=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mlas_classification_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["record_id"]
        indexes = [
            models.Index(fields=["review_status", "confidence_overall"]),
            models.Index(fields=["mlas_subject_code", "mlas_branch_code", "mlas_term_code"]),
            models.Index(fields=["target_layer", "review_status"]),
        ]

    def __str__(self):
        return f"{self.record_id} {self.basetrue_label or self.source_name_raw}".strip()

    def clean(self):
        errors = {}

        scores = [
            float(self.algorithm_1_score or 0.0),
            float(self.algorithm_2_score or 0.0),
            float(self.algorithm_3_score or 0.0),
            float(self.algorithm_4_score or 0.0),
        ]
        self.algorithm_consensus_score = round(sum(scores) / 4.0, 6)

        if not (self.dewey_code or self.gics_sub_industry_code or self.naics_code_6):
            errors["dewey_code"] = "Provide at least one external classification link (Dewey, GICS sub-industry, or NAICS-6)."

        if self.review_status == self.REVIEW_APPROVED:
            if not self.mlas_branch_code:
                errors["mlas_branch_code"] = "Approved rows require mlas_branch_code."
            if not self.mlas_term_code:
                errors["mlas_term_code"] = "Approved rows require mlas_term_code."
            if not self.reviewer_id:
                errors["reviewer"] = "Approved rows require reviewer."
            if not self.reviewed_at:
                errors["reviewed_at"] = "Approved rows require reviewed_at timestamp."

        if self.target_layer == self.TARGET_META and not self.mlas_meta_term_code:
            errors["mlas_meta_term_code"] = "Meta target layer requires mlas_meta_term_code."

        if self.target_layer == self.TARGET_TERM and self.mlas_meta_term_code:
            errors["mlas_meta_term_code"] = "Term target layer must not set mlas_meta_term_code."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class Slide(models.Model):
    # Raw metadata fields
    title = models.CharField(max_length=200, db_index=True)

    phase = models.CharField(
        max_length=20,
        choices=[
            ("create", "Create"),
            ("post", "Post"),
            ("work", "Work"),
        ],
        db_index=True,
    )

    color_primary = models.CharField(
        max_length=20,
        choices=[
            ("red", "Red"),
            ("blue", "Blue"),
            ("yellow", "Yellow"),
            ("green", "Green"),
            ("purple", "Purple"),
            ("teal", "Teal"),
            ("orange", "Orange"),
            ("lime", "Lime"),
            ("pink", "Pink"),
            ("cyan", "Cyan"),
            ("amber", "Amber"),
            ("green-lime", "Green-Lime"),
        ],
        db_index=True,
    )

    metaphor = models.CharField(
        max_length=30,
        choices=[
            ("immune_system", "Immune System"),
            ("mycelium", "Mycelium"),
            ("botanist", "Botanist"),
        ],
        db_index=True,
    )

    # MLAS hierarchy
    mlas_subject = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_branch = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_term = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    mlas_meta = models.CharField(max_length=30, blank=True, null=True, db_index=True)

    # Dewey sync
    dewey_code = models.IntegerField(db_index=True)

    # Industry mapping
    industry_super_sector = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    industry_sector = models.CharField(max_length=100, blank=True, null=True)
    industry_group = models.CharField(max_length=100, blank=True, null=True)
    industry_sub_industry = models.CharField(max_length=100, blank=True, null=True)

    # UI category (raw)
    ui_category = models.CharField(
        max_length=30,
        choices=[
            ("operations", "Operations"),
            ("customer", "Customer"),
            ("delivery", "Delivery"),
            ("executive", "Executive"),
        ],
        blank=True,
        null=True,
        db_index=True,
    )

    # Resolver-derived fields
    phase_resolved = models.CharField(max_length=20, db_index=True)
    ui_category_resolved = models.CharField(max_length=30, db_index=True)
    layout_archetype = models.CharField(max_length=30, db_index=True)
    component_pack = models.CharField(max_length=30, db_index=True)
    nav_group = models.CharField(max_length=30, db_index=True)
    page_signature = models.CharField(max_length=50, db_index=True)

    # Preset reference
    applied_preset = models.ForeignKey(
        "SemanticPreset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slides",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["phase"]),
            models.Index(fields=["color_primary"]),
            models.Index(fields=["mlas_subject", "mlas_branch", "mlas_term"]),
            models.Index(fields=["dewey_code"]),
            models.Index(fields=["industry_super_sector"]),
            models.Index(fields=["ui_category_resolved"]),
        ]
