import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from project_middle_layer.models import ProjectNode, SemanticPipeline, SemanticPipelineRun, SemanticSchedule, SemanticScheduleRun


class ProjectMiddleLayerSemanticCLITests(TestCase):
    def _run_command(self, *args):
        stdout = StringIO()
        call_command("project_middle_layer_semantic", *args, stdout=stdout)
        lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertTrue(lines)
        return json.loads(lines[-1])

    def test_cli_compile_action_creates_project(self):
        result = self._run_command(
            "compile",
            "--payload-json",
            json.dumps(
                {
                    "title": "CLI Compile Project",
                    "intent": "community_program",
                    "tier": "public",
                    "tags": ["cli", "compile"],
                }
            ),
        )

        self.assertEqual(result["action"], "compile")
        self.assertEqual(result["project"]["slug"], "cli-compile-project")
        self.assertEqual(ProjectNode.objects.filter(slug="cli-compile-project").count(), 1)

    def test_cli_batch_compile_action_compiles_multiple_projects(self):
        result = self._run_command(
            "batch-compile",
            "--payload-json",
            json.dumps(
                {
                    "projects": [
                        {
                            "title": "CLI Batch One",
                            "intent": "community_program",
                            "tier": "public",
                            "tags": ["cli", "batch"],
                        },
                        {
                            "title": "CLI Batch Two",
                            "intent": "education_flow",
                            "tier": "public",
                            "tags": ["cli", "batch"],
                        },
                    ]
                }
            ),
        )

        self.assertEqual(result["action"], "batch-compile")
        self.assertEqual(result["summary"]["requested"], 2)
        self.assertEqual(result["summary"]["compiled"], 2)
        self.assertEqual(ProjectNode.objects.filter(slug="cli-batch-one").count(), 1)
        self.assertEqual(ProjectNode.objects.filter(slug="cli-batch-two").count(), 1)

    def test_cli_diff_action_returns_diff_payload(self):
        result = self._run_command(
            "diff",
            "--source-json",
            json.dumps(
                {
                    "identity_uri": "cpndc://project/source",
                    "semantic_tags": ["one", "two"],
                    "drift_risk": 0.2,
                    "confidence_score": 80,
                    "stability_score": 78,
                    "branch_name": "stabilization_branch",
                    "final_identity_uri": "cpndc://final/source",
                }
            ),
            "--target-json",
            json.dumps(
                {
                    "identity_uri": "cpndc://project/target",
                    "semantic_tags": ["two", "three"],
                    "drift_risk": 0.45,
                    "confidence_score": 70,
                    "stability_score": 68,
                    "branch_name": "expansion_integration_branch",
                    "final_identity_uri": "cpndc://final/target",
                }
            ),
        )

        self.assertEqual(result["action"], "diff")
        self.assertEqual(result["diff"]["tag_changes"]["added"], ["three"])
        self.assertEqual(result["diff"]["tag_changes"]["removed"], ["one"])

    def test_cli_export_action_returns_summary(self):
        ProjectNode.objects.create(
            slug="cli-export-project",
            name="CLI Export Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["cli", "export"]},
        )

        result = self._run_command("export", "--scope", "all", "--max-items", "50")

        self.assertEqual(result["action"], "export")
        self.assertIn("project_count", result["summary"])
        self.assertGreaterEqual(result["summary"]["project_count"], 1)

    def test_cli_pipeline_run_action_executes_pipeline(self):
        SemanticPipeline.objects.create(
            name="CLI Pipeline",
            slug="cli-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "CLI Pipeline Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["cli", "pipeline"],
                    },
                }
            ],
            triggers={"mode": "manual"},
            is_active=True,
        )

        result = self._run_command("pipeline-run", "--pipeline-slug", "cli-pipeline")

        self.assertEqual(result["action"], "pipeline-run")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="cli-pipeline-project").count(), 1)
        self.assertEqual(SemanticPipelineRun.objects.filter(pipeline__slug="cli-pipeline").count(), 1)

    def test_cli_schedule_run_action_executes_schedule(self):
        pipeline = SemanticPipeline.objects.create(
            name="CLI Schedule Pipeline",
            slug="cli-schedule-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "CLI Schedule Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["cli", "schedule"],
                    },
                }
            ],
            triggers={"mode": "manual"},
            is_active=True,
        )
        SemanticSchedule.objects.create(
            name="CLI Schedule",
            slug="cli-schedule",
            cron_expression="*/30 * * * *",
            action="pipeline-run",
            pipeline=pipeline,
            payload={},
            is_paused=False,
        )

        result = self._run_command("schedule-run", "--schedule-slug", "cli-schedule")

        self.assertEqual(result["action"], "schedule-run")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="cli-schedule-project").count(), 1)
        self.assertEqual(SemanticScheduleRun.objects.filter(schedule__slug="cli-schedule").count(), 1)

    def test_cli_batch_compile_atomic_rolls_back_on_validation_error(self):
        with self.assertRaises(CommandError):
            self._run_command(
                "batch-compile",
                "--payload-json",
                json.dumps(
                    {
                        "projects": [
                            {
                                "title": "CLI Atomic Good",
                                "intent": "community_program",
                                "tier": "public",
                                "tags": ["cli", "atomic"],
                            },
                            {
                                "title": "CLI Atomic Bad",
                                "tier": "public",
                                "tags": ["cli", "atomic"],
                            },
                        ]
                    }
                ),
                "--atomic",
            )

        self.assertEqual(ProjectNode.objects.filter(slug="cli-atomic-good").count(), 0)
