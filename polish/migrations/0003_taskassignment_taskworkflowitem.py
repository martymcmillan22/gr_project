from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("polish", "0002_polishreminderpreference"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "assignment_type",
                    models.CharField(
                        choices=[
                            ("linear", "Linear Assignment"),
                            ("double_linear", "2x Linear Assignment"),
                            ("twelve_point", "12-Point Assignment"),
                            ("perpetual", "Perpetual Assignment"),
                        ],
                        default="linear",
                        max_length=32,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("current_step_index", models.PositiveSmallIntegerField(default=0)),
                ("current_phase", models.CharField(default="create", max_length=16)),
                ("current_compartment", models.CharField(default="R", max_length=8)),
                ("is_closed", models.BooleanField(default=False)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_task_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-updated_at", "-created_at")},
        ),
        migrations.CreateModel(
            name="TaskWorkflowItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "assignment_type",
                    models.CharField(
                        choices=[
                            ("linear", "Linear Assignment"),
                            ("double_linear", "2x Linear Assignment"),
                            ("twelve_point", "12-Point Assignment"),
                            ("perpetual", "Perpetual Assignment"),
                        ],
                        default="linear",
                        max_length=32,
                    ),
                ),
                (
                    "status",
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
                ("current_step_index", models.PositiveSmallIntegerField(default=0)),
                ("current_phase", models.CharField(default="create", max_length=16)),
                ("current_compartment", models.CharField(default="R", max_length=8)),
                ("object_id", models.PositiveBigIntegerField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflow_items",
                        to="polish.taskassignment",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype"),
                ),
            ],
            options={"ordering": ("-updated_at", "-created_at")},
        ),
        migrations.AddConstraint(
            model_name="taskworkflowitem",
            constraint=models.UniqueConstraint(
                fields=("assignment", "content_type", "object_id"),
                name="ux_task_workflow_item_assignment_object",
            ),
        ),
    ]
