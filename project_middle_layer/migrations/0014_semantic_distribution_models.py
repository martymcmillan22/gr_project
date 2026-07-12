from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0013_semantic_collaboration_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReplicationConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("remote_node_url", models.URLField(max_length=500)),
                ("api_key", models.CharField(max_length=128)),
                ("mode", models.CharField(choices=[("full", "Full Replication"), ("branch_only", "Branch Only"), ("tier_only", "Tier Only"), ("snapshot_only", "Snapshot Only")], default="full", max_length=32)),
                ("direction", models.CharField(choices=[("push", "Push"), ("pull", "Pull"), ("bidirectional", "Bidirectional")], default="bidirectional", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("last_synced_version", models.PositiveIntegerField(default=0)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(default="idle", max_length=20)),
                ("last_error", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="FederationPeer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("peer_identity", models.CharField(max_length=255)),
                ("peer_url", models.URLField(max_length=500)),
                ("capabilities", models.JSONField(blank=True, default=list)),
                ("sync_rules", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(default="idle", max_length=20)),
                ("last_error", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SemanticShard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("node_url", models.URLField(blank=True, max_length=500)),
                ("strategy", models.CharField(choices=[("branch", "By Branch"), ("tier", "By Tier"), ("slug_prefix", "By Project Slug Prefix"), ("cluster", "By Semantic Cluster")], default="branch", max_length=32)),
                ("route_value", models.CharField(blank=True, max_length=120)),
                ("project_slug_prefix", models.CharField(blank=True, max_length=20)),
                ("cluster_label", models.CharField(blank=True, max_length=120)),
                ("branch", models.CharField(blank=True, max_length=120)),
                ("tier", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("health_score", models.PositiveSmallIntegerField(default=100)),
                ("status", models.CharField(default="healthy", max_length=20)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SemanticSyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sync_type", models.CharField(choices=[("version", "Version Sync"), ("snapshot", "Snapshot Sync"), ("lineage", "Lineage Sync"), ("tag", "Tag Sync"), ("alert", "Alert/Recommendation Sync")], max_length=20)),
                ("source_node", models.CharField(blank=True, max_length=255)),
                ("target_node", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="running", max_length=20)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-started_at", "-id"]},
        ),
        migrations.CreateModel(
            name="DistributedAgentRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("agent_name", models.CharField(max_length=120)),
                ("node_count", models.PositiveIntegerField(default=0)),
                ("shard_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("completed", "Completed"), ("failed", "Failed")], default="completed", max_length=20)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("insights", models.JSONField(blank=True, default=list)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
