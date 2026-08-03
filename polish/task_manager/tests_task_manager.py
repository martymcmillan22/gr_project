from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from center.models import CorporationItem
from polish.models import TaskAssignment
from polish.models import TaskWorkflowDriftSnapshot
from polish.task_manager.assignment_engine import build_assignment_sequence
from polish.task_manager.constants import (
    ASSIGNMENT_DOUBLE_LINEAR,
    ASSIGNMENT_LINEAR,
    ASSIGNMENT_PERPETUAL,
    ASSIGNMENT_TWELVE_POINT,
    ITEM_STATUS_COMPLETED,
)
from polish.task_manager.constants import get_task_archetype_definition
from polish.task_manager.routing import (
    build_middle_layer_compartment_drift_detection,
    build_polish_compartment_refinement,
    build_va_compartment_narration,
    bind_deliverable_to_compartments,
    get_phase_policy,
    resolve_assignment_type_for_deliverable,
    task_manager_enabled_for_phase,
)
from polish.task_manager.workflow_tracking import (
    advance_item,
    attach_item,
    complete_item_early,
    create_assignment,
    resume_item,
    skip_item_to_step,
)
from seeds.models import Idea
from peringram.models import Industry, IndustryGroup


class TaskManagerSequenceTests(TestCase):
    def test_canonical_archetype_definitions_have_expected_compartment_counts(self):
        self.assertEqual(get_task_archetype_definition(ASSIGNMENT_LINEAR)["compartment_count"], 4)
        self.assertEqual(get_task_archetype_definition(ASSIGNMENT_DOUBLE_LINEAR)["compartment_count"], 8)
        self.assertEqual(get_task_archetype_definition(ASSIGNMENT_TWELVE_POINT)["compartment_count"], 12)
        self.assertEqual(get_task_archetype_definition(ASSIGNMENT_PERPETUAL)["compartment_count"], 24)

    def test_sequence_lengths_match_assignment_definitions(self):
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_LINEAR)), 4)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_DOUBLE_LINEAR)), 8)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_TWELVE_POINT)), 12)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_PERPETUAL)), 24)

    def test_canonical_track_compartment_maps_have_expected_counts(self):
        linear = get_task_archetype_definition(ASSIGNMENT_LINEAR)
        self.assertEqual(len(linear["canonical_compartments"]["track_a"]), 4)

        double_linear = get_task_archetype_definition(ASSIGNMENT_DOUBLE_LINEAR)
        self.assertEqual(len(double_linear["canonical_compartments"]["track_a"]), 4)
        self.assertEqual(len(double_linear["canonical_compartments"]["track_b"]), 4)

        twelve_point = get_task_archetype_definition(ASSIGNMENT_TWELVE_POINT)
        self.assertEqual(len(twelve_point["canonical_compartments"]["track_a"]), 12)

        perpetual = get_task_archetype_definition(ASSIGNMENT_PERPETUAL)
        self.assertEqual(len(perpetual["canonical_compartments"]["track_a"]), 12)
        self.assertEqual(len(perpetual["canonical_compartments"]["track_b"]), 12)

    def test_perpetual_restarts_compartment_count_on_second_cycle(self):
        sequence = build_assignment_sequence(ASSIGNMENT_PERPETUAL)
        self.assertEqual(sequence[0].compartment, "R")
        self.assertEqual(sequence[11].compartment, "G-L")
        self.assertEqual(sequence[12].compartment, "R")
        self.assertEqual(sequence[12].cycle, 2)

    def test_deliverable_routing_maps_to_expected_assignment_types(self):
        self.assertEqual(resolve_assignment_type_for_deliverable("Monthly issue"), ASSIGNMENT_LINEAR)
        self.assertEqual(resolve_assignment_type_for_deliverable("Issue with sidebar"), ASSIGNMENT_DOUBLE_LINEAR)
        self.assertEqual(resolve_assignment_type_for_deliverable("Annual summary"), ASSIGNMENT_TWELVE_POINT)
        self.assertEqual(resolve_assignment_type_for_deliverable("Annual plan"), ASSIGNMENT_PERPETUAL)
        self.assertEqual(resolve_assignment_type_for_deliverable("Editorial calendar"), ASSIGNMENT_PERPETUAL)
        self.assertEqual(resolve_assignment_type_for_deliverable("Theme tracker"), ASSIGNMENT_PERPETUAL)

    def test_phase_policy_gates_task_manager_to_project_phase(self):
        self.assertFalse(task_manager_enabled_for_phase("idea"))
        self.assertFalse(task_manager_enabled_for_phase("seed"))
        self.assertTrue(task_manager_enabled_for_phase("project"))

        seed_policy = get_phase_policy("seed")
        self.assertEqual(seed_policy["va"]["mode"], "read_only")
        self.assertFalse(seed_policy["task_manager"]["enabled"])

    def test_compartment_binding_shape_is_deterministic(self):
        bound = bind_deliverable_to_compartments(
            assignment_type=ASSIGNMENT_DOUBLE_LINEAR,
            deliverable_name="Issue with sidebar",
        )
        self.assertEqual(bound["progression_model"], "parallel")
        self.assertEqual(bound["binding_count"], 8)
        self.assertEqual(len(bound["compartment_bindings"]), 8)

    def test_compartment_governance_builders_return_expected_shapes(self):
        drift = build_middle_layer_compartment_drift_detection(
            assignment_type=ASSIGNMENT_LINEAR,
            deliverable_name="Monthly issue",
            drift_risk=0.4,
            alert_count=2,
        )
        va = build_va_compartment_narration(
            assignment_type=ASSIGNMENT_LINEAR,
            deliverable_name="Monthly issue",
            drift_detection=drift,
        )
        polish = build_polish_compartment_refinement(
            assignment_type=ASSIGNMENT_LINEAR,
            deliverable_name="Monthly issue",
        )

        self.assertEqual(len(drift["compartments"]), 4)
        self.assertEqual(len(va["compartments"]), 4)
        self.assertEqual(len(polish["compartments"]), 4)
        self.assertIn("next_step", va["compartments"][0])
        self.assertIn("clarity", polish["compartments"][0]["refinement"])
        self.assertIn("semantic", drift["compartments"][0]["drift"])


class TaskManagerWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.botanist = user_model.objects.create_user(
            username="botanist",
            email="botanist@example.com",
            password="testpass123",
            name="Botanist User",
        )
        self.engineer = user_model.objects.create_user(
            username="engineer",
            email="engineer@example.com",
            password="testpass123",
            name="Engineer User",
        )
        self.architect = user_model.objects.create_user(
            username="architect",
            email="architect@example.com",
            password="testpass123",
            name="Architect User",
            subscription_tier=user_model.SUBSCRIPTION_PREMIUM_PRO,
        )

        Group.objects.get_or_create(name="botanists")[0].user_set.add(self.botanist)
        Group.objects.get_or_create(name="engineers")[0].user_set.add(self.engineer)
        Group.objects.get_or_create(name="architects")[0].user_set.add(self.architect)

        self.group = IndustryGroup.objects.create(code=1, name="Math", sector=IndustryGroup.SECTOR_PRIMARY)
        self.industry = Industry.objects.create(group=self.group, code=1, name="Food Tech")
        self.idea = Idea.objects.create(
            user=self.engineer,
            industry=self.industry,
            raw_content="Idea to seed to project",
        )
        self.corporation_item = CorporationItem.objects.create(
            owner=self.engineer,
            title="Corporation workflow item",
            description="Track through assignment engine",
        )

    def test_role_permissions_enforced_for_assignment_creation(self):
        assignment = create_assignment(
            created_by=self.botanist,
            assignment_type=ASSIGNMENT_LINEAR,
            title="Botanist linear",
            assigned_to=self.engineer,
        )
        self.assertEqual(assignment.assignment_type, ASSIGNMENT_LINEAR)

        with self.assertRaisesMessage(Exception, "User cannot create this assignment type"):
            create_assignment(
                created_by=self.botanist,
                assignment_type=ASSIGNMENT_TWELVE_POINT,
                title="Botanist twelve",
                assigned_to=self.engineer,
            )

        architect_assignment = create_assignment(
            created_by=self.architect,
            assignment_type=ASSIGNMENT_PERPETUAL,
            title="Architect perpetual",
            assigned_to=self.engineer,
        )
        self.assertEqual(architect_assignment.assignment_type, ASSIGNMENT_PERPETUAL)

    def test_item_can_skip_steps_and_remain_sequential(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type=ASSIGNMENT_TWELVE_POINT,
            title="Seed workflow",
            assigned_to=self.engineer,
        )
        item = attach_item(assignment=assignment, workflow_object=self.idea)

        progress = skip_item_to_step(item=item, step_index=5)
        self.assertEqual(progress.step_index, 5)
        self.assertEqual(progress.phase, "post")
        self.assertEqual(progress.compartment, "T")

        next_progress = advance_item(item=item, steps=1)
        self.assertEqual(next_progress.step_index, 6)
        self.assertEqual(next_progress.compartment, "O")

    def test_early_completion_and_resume_support_partial_traversal(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type=ASSIGNMENT_DOUBLE_LINEAR,
            title="Corp assignment",
            assigned_to=self.engineer,
        )
        item = attach_item(assignment=assignment, workflow_object=self.corporation_item)

        advance_item(item=item, steps=2)
        complete_item_early(item=item)
        item.refresh_from_db()
        self.assertEqual(item.status, ITEM_STATUS_COMPLETED)

        resume_item(item=item)
        item.refresh_from_db()
        self.assertNotEqual(item.status, ITEM_STATUS_COMPLETED)

        final_progress = advance_item(item=item, steps=20)
        self.assertTrue(final_progress.completed)
        item.refresh_from_db()
        self.assertEqual(item.status, ITEM_STATUS_COMPLETED)

    def test_drift_ledger_records_advance_skip_complete_resume_events(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type=ASSIGNMENT_LINEAR,
            title="Ledger assignment",
            assigned_to=self.engineer,
        )
        item = attach_item(assignment=assignment, workflow_object=self.idea)

        advance_item(item=item, steps=1)
        skip_item_to_step(item=item, step_index=2)
        complete_item_early(item=item)
        resume_item(item=item)

        events = list(TaskWorkflowDriftSnapshot.objects.filter(assignment=assignment).order_by("created_at", "id"))
        self.assertEqual(len(events), 4)
        self.assertEqual(events[0].event_type, TaskWorkflowDriftSnapshot.EVENT_ADVANCE)
        self.assertEqual(events[1].event_type, TaskWorkflowDriftSnapshot.EVENT_SKIP)
        self.assertEqual(events[2].event_type, TaskWorkflowDriftSnapshot.EVENT_COMPLETE)
        self.assertEqual(events[3].event_type, TaskWorkflowDriftSnapshot.EVENT_RESUME)
        self.assertIn("slot_drift", events[0].drift_payload)

    def test_assignment_records_current_position(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type=ASSIGNMENT_LINEAR,
            title="Linear current position",
            assigned_to=self.engineer,
        )
        self.assertEqual(assignment.current_phase, "create")
        self.assertEqual(assignment.current_compartment, "R")
        self.assertEqual(assignment.metadata["task_archetype"]["compartment_count"], 4)
        self.assertEqual(assignment.metadata["task_archetype"]["tracks"], 1)
        self.assertEqual(assignment.metadata["task_archetype"]["progression_model"], "sequential")
        self.assertEqual(assignment.metadata["phase_policy"]["phase"], "project")
        self.assertEqual(assignment.metadata["deliverable_routing"]["assignment_type"], ASSIGNMENT_LINEAR)
        self.assertIn("compartment_governance", assignment.metadata)
        self.assertIn("va_narration", assignment.metadata["compartment_governance"])
        self.assertIn("polish_refinement", assignment.metadata["compartment_governance"])
        self.assertIn("middle_layer_drift_detection", assignment.metadata["compartment_governance"])
        self.assertEqual(TaskAssignment.objects.count(), 1)

    def test_assignment_creation_blocked_outside_project_phase(self):
        with self.assertRaisesMessage(Exception, "Task Manager assignments are only allowed in the Project phase"):
            create_assignment(
                created_by=self.engineer,
                assignment_type=ASSIGNMENT_LINEAR,
                title="Blocked in seed",
                assigned_to=self.engineer,
                operating_phase="seed",
            )

    def test_assignment_creation_auto_routes_from_deliverable_name(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type="auto",
            title="Auto routed",
            assigned_to=self.engineer,
            deliverable_name="Issue with sidebar",
        )
        self.assertEqual(assignment.assignment_type, ASSIGNMENT_DOUBLE_LINEAR)
        self.assertEqual(assignment.metadata["deliverable_routing"]["progression_model"], "parallel")
