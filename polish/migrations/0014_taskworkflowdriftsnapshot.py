from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0013_alter_taskattachmentauditlog_event_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskWorkflowDriftSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("advance", "Advance"),
                            ("skip", "Skip"),
                            ("complete", "Complete"),
                            ("resume", "Resume"),
                        ],
                        max_length=16,
                    ),
                ),
                ("slot_key", models.CharField(max_length=64)),
                ("from_step_index", models.PositiveSmallIntegerField(default=0)),
                ("to_step_index", models.PositiveSmallIntegerField(default=0)),
                ("from_phase", models.CharField(default="create", max_length=16)),
                ("to_phase", models.CharField(default="create", max_length=16)),
                ("from_compartment", models.CharField(default="R", max_length=8)),
                ("to_compartment", models.CharField(default="R", max_length=8)),
                (
                    "status_before",
                    models.CharField(
                        choices=[
                            ("received", "Received"),
                            ("working", "Working"),
                            ("completed", "Completed"),
                        ],
                        default="received",
                        max_length=16,
                    ),
                ),
                (
                    "status_after",
                    models.CharField(
                        choices=[
                            ("received", "Received"),
                            ("working", "Working"),
                            ("completed", "Completed"),
                        ],
                        default="received",
                        max_length=16,
                    ),
                ),
                ("drift_payload", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drift_snapshots",
                        to="polish.taskassignment",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drift_snapshots",
                        to="polish.taskworkflowitem",
                    ),
                ),
            ],
            options={"ordering": ("created_at", "id")},
        ),
        migrations.AddIndex(
            model_name="taskworkflowdriftsnapshot",
            index=models.Index(fields=["assignment", "created_at"], name="idx_task_drift_assignment_ts"),
        ),
        migrations.AddIndex(
            model_name="taskworkflowdriftsnapshot",
            index=models.Index(fields=["item", "created_at"], name="idx_task_drift_item_ts"),
        ),
        migrations.AddIndex(
            model_name="taskworkflowdriftsnapshot",
            index=models.Index(fields=["assignment", "slot_key", "created_at"], name="idx_task_drift_slot_ts"),
        ),
    ]
