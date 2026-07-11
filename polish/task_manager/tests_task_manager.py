from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from center.models import CorporationItem
from polish.models import TaskAssignment
from polish.task_manager.assignment_engine import build_assignment_sequence
from polish.task_manager.constants import (
    ASSIGNMENT_DOUBLE_LINEAR,
    ASSIGNMENT_LINEAR,
    ASSIGNMENT_PERPETUAL,
    ASSIGNMENT_TWELVE_POINT,
    ITEM_STATUS_COMPLETED,
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
    def test_sequence_lengths_match_assignment_definitions(self):
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_LINEAR)), 4)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_DOUBLE_LINEAR)), 8)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_TWELVE_POINT)), 12)
        self.assertEqual(len(build_assignment_sequence(ASSIGNMENT_PERPETUAL)), 24)

    def test_perpetual_restarts_compartment_count_on_second_cycle(self):
        sequence = build_assignment_sequence(ASSIGNMENT_PERPETUAL)
        self.assertEqual(sequence[0].compartment, "R")
        self.assertEqual(sequence[11].compartment, "G-L")
        self.assertEqual(sequence[12].compartment, "R")
        self.assertEqual(sequence[12].cycle, 2)


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

    def test_assignment_records_current_position(self):
        assignment = create_assignment(
            created_by=self.engineer,
            assignment_type=ASSIGNMENT_LINEAR,
            title="Linear current position",
            assigned_to=self.engineer,
        )
        self.assertEqual(assignment.current_phase, "create")
        self.assertEqual(assignment.current_compartment, "R")
        self.assertEqual(TaskAssignment.objects.count(), 1)
