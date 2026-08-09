from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from io import StringIO
import tempfile
from pathlib import Path
from unittest.mock import patch

from peringram.models import Industry, IndustryGroup
from seeds.models import Idea

from .models import (
	PolishTask,
	SectorAgenda,
	PolishReminderPreference,
	TaskAssignment,
	TaskAssignmentAttachment,
	TaskAttachmentAuditLog,
	TaskAttachmentQuarantine,
	TaskManagerAnalyticsExportRun,
	TaskWorkflowDriftSnapshot,
	TaskWorkflowItem,
)
from .admin import TaskAttachmentQuarantineAdmin


class PolishDashboardTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="polishuser@example.com",
			email="polishuser@example.com",
			password="testpass123",
			first_name="Polish",
			last_name="User",
		)

	def test_dashboard_requires_login(self):
		response = self.client.get(reverse("polish:dashboard"))
		self.assertEqual(response.status_code, 302)

	def test_staff_user_can_access_polish_dashboard(self):
		polish_admin_group, _ = Group.objects.get_or_create(name="polish_admin")
		polish_admin_group.user_set.add(self.user)
		self.client.force_login(self.user)
		response = self.client.get(reverse("polish:dashboard"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "<h1 class=\"title is-3\">Polish</h1>")

	def test_polish_admin_group_does_not_grant_django_admin_access(self):
		polish_admin_group, _ = Group.objects.get_or_create(name="polish_admin")
		polish_admin_group.user_set.add(self.user)
		self.client.force_login(self.user)
		response = self.client.get("/admin/")
		self.assertNotEqual(response.status_code, 200)

	def test_unfinished_task_reminder_shows(self):
		self.client.login(username="polishuser@example.com", password="testpass123")
		response = self.client.get(reverse("polish:dashboard"))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("center:corporation_admin"), response["Location"])

	def test_mark_task_complete_removes_unfinished_reminder(self):
		self.client.login(username="polishuser@example.com", password="testpass123")
		task = PolishTask.objects.create(user=self.user, title="Draft outreach plan")
		response = self.client.post(
			reverse("polish:dashboard"),
			{"action": "complete_task", "task_id": str(task.id)},
		)
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("center:corporation_admin"), response["Location"])

	def test_create_agenda_from_sector_and_idea(self):
		self.client.login(username="polishuser@example.com", password="testpass123")
		response = self.client.post(
			reverse("polish:dashboard"),
			{
				"action": "create_agenda",
				"sector_name": "Healthcare",
				"idea": "Remote diagnostics platform",
				"objective": "Launch pilot with two clinics",
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("center:corporation_admin"), response["Location"])

	def test_user_can_opt_in_for_daily_twist_reminders(self):
		self.client.login(username="polishuser@example.com", password="testpass123")
		response = self.client.post(
			reverse("polish:dashboard"),
			{
				"action": "update_reminder_preference",
				"enabled": "on",
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("center:corporation_admin"), response["Location"])


class PolishTaskManagerIntegrationTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="engineer@example.com",
			email="engineer@example.com",
			password="testpass123",
			first_name="Engineer",
			last_name="User",
		)
		group, _ = Group.objects.get_or_create(name="engineers")
		group.user_set.add(self.user)
		polish_admin_group, _ = Group.objects.get_or_create(name="polish_admin")
		polish_admin_group.user_set.add(self.user)

		self.group = IndustryGroup.objects.create(code=1, name="Math", sector=IndustryGroup.SECTOR_PRIMARY)
		self.industry = Industry.objects.create(group=self.group, code=1, name="Food Tech")
		self.idea = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="workflow idea",
		)

	def test_dashboard_renders_task_manager_panel(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.get(reverse("polish:dashboard"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Task Manager")

	def test_dedicated_task_manager_admin_page_loads(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		TaskAssignment.objects.create(
			title="Timeline Control Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)
		response = self.client.get(reverse("task-manager-admin:index"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Task Manager Admin")
		self.assertContains(response, "Task Manager Metrics")
		self.assertContains(response, "Total Assignments")
		self.assertContains(response, "Governance Timeline")
		self.assertContains(response, "Event Type")
		self.assertContains(response, "Grouped by item for replay and audit readability")
		self.assertContains(response, "Risk Rollup")
		self.assertNotContains(response, 'name="visibility"')

	def test_task_manager_admin_metrics_tab_query_is_honored(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.get(f"{reverse('task-manager-admin:index')}?active_tab=metrics")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'data-active-tab="metrics"')

	def test_task_manager_metrics_api_returns_expected_shape(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.get(reverse("task-manager-metrics-api"))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("total_assignments", payload)
		self.assertIn("phase_counts", payload)
		self.assertIn("compartment_counts", payload)
		self.assertIn("compartment_slots", payload)
		self.assertIn("assignment_timeline", payload)
		self.assertIn("item_lifecycle_heatmap", payload)
		self.assertIn("compartment_flow", payload)
		self.assertEqual(len(payload["assignment_timeline"]), 7)
		self.assertEqual(len(payload["compartment_slots"]), 12)
		slot_codes = [slot.get("code") for slot in payload["compartment_slots"]]
		self.assertIn("PI", slot_codes)
		self.assertIn("PU", slot_codes)
		self.assertEqual(slot_codes[4], "PU")
		self.assertEqual(slot_codes[8], "PI")

	def test_task_manager_activity_api_returns_events_list(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.get(reverse("task-manager-activity-api"))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("events", payload)
		self.assertIsInstance(payload["events"], list)

	def test_task_manager_assignment_timeline_api_returns_replay_events(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Timeline Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)
		item = TaskWorkflowItem.objects.create(
			assignment=assignment,
			content_type=ContentType.objects.get_for_model(Idea),
			object_id=self.idea.id,
		)
		TaskWorkflowDriftSnapshot.objects.create(
			assignment=assignment,
			item=item,
			slot_key="create:R:s1",
			event_type="advance",
			from_step_index=0,
			to_step_index=1,
			from_phase="create",
			to_phase="create",
			from_compartment="R",
			to_compartment="B",
			status_before="received",
			status_after="working",
			drift_payload={"slot_drift": {"status": "stable"}},
		)

		response = self.client.get(reverse("task-manager-assignment-timeline-api", args=[assignment.id]))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["assignment"]["id"], assignment.id)
		self.assertEqual(payload["event_count"], 1)
		self.assertEqual(payload["events"][0]["event_type"], "advance")
		self.assertIn("drift", payload["events"][0])
		self.assertIn(str(item.id), payload["item_trends"])
		self.assertIn("status", payload["item_trends"][str(item.id)])

	def test_task_manager_assignment_timeline_api_filters(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Timeline Filter Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)
		item = TaskWorkflowItem.objects.create(
			assignment=assignment,
			content_type=ContentType.objects.get_for_model(Idea),
			object_id=self.idea.id,
		)
		TaskWorkflowDriftSnapshot.objects.create(
			assignment=assignment,
			item=item,
			slot_key="create:R:s1",
			event_type="advance",
			from_step_index=0,
			to_step_index=1,
			from_phase="create",
			to_phase="create",
			from_compartment="R",
			to_compartment="B",
			status_before="received",
			status_after="working",
			drift_payload={"slot_drift": {"status": "stable"}},
		)
		TaskWorkflowDriftSnapshot.objects.create(
			assignment=assignment,
			item=item,
			slot_key="post:T:s5",
			event_type="skip",
			from_step_index=1,
			to_step_index=4,
			from_phase="create",
			to_phase="post",
			from_compartment="B",
			to_compartment="T",
			status_before="working",
			status_after="working",
			drift_payload={"slot_drift": {"status": "watch"}},
		)

		response = self.client.get(
			reverse("task-manager-assignment-timeline-api", args=[assignment.id]),
			{"event_type": "skip", "slot_prefix": "post", "limit": "10"},
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["event_count"], 1)
		self.assertEqual(payload["events"][0]["event_type"], "skip")
		self.assertTrue(payload["events"][0]["slot_key"].startswith("post"))

	def test_staff_can_download_operational_analytics_csv_and_pdf(self):
		self.client.force_login(self.user)

		csv_response = self.client.get(reverse("polish:task-manager:export-analytics-csv"))
		self.assertEqual(csv_response.status_code, 200)
		self.assertIn("text/csv", csv_response["Content-Type"])
		self.assertIn("attachment;", csv_response["Content-Disposition"])
		self.assertIn("assignment_throughput_7d", csv_response.content.decode("utf-8"))

		pdf_response = self.client.get(reverse("polish:task-manager:export-analytics-pdf"))
		self.assertEqual(pdf_response.status_code, 200)
		self.assertIn("application/pdf", pdf_response["Content-Type"])

		export_runs = TaskManagerAnalyticsExportRun.objects.filter(requested_by=self.user)
		self.assertEqual(export_runs.count(), 2)
		self.assertTrue(export_runs.filter(export_format="csv").exists())
		self.assertTrue(export_runs.filter(export_format="pdf").exists())

	@patch("polish.views._build_task_manager_metrics")
	def test_failed_csv_export_creates_failed_history_row(self, mock_build_task_manager_metrics):
		self.client.force_login(self.user)
		mock_build_task_manager_metrics.side_effect = RuntimeError("simulated csv failure")

		response = self.client.get(reverse("polish:task-manager:export-analytics-csv"))

		self.assertEqual(response.status_code, 302)
		failed_run = TaskManagerAnalyticsExportRun.objects.filter(
			requested_by=self.user,
			export_format=TaskManagerAnalyticsExportRun.FORMAT_CSV,
			status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
		).first()
		self.assertIsNotNone(failed_run)
		self.assertIn("simulated csv failure", failed_run.error_message)

	def test_export_history_failed_only_filter(self):
		self.client.force_login(self.user)

		TaskManagerAnalyticsExportRun.objects.create(
			requested_by=self.user,
			target_user=self.user,
			trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
			export_format=TaskManagerAnalyticsExportRun.FORMAT_CSV,
			status=TaskManagerAnalyticsExportRun.STATUS_SUCCESS,
			notes="success marker",
		)
		TaskManagerAnalyticsExportRun.objects.create(
			requested_by=self.user,
			target_user=self.user,
			trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
			export_format=TaskManagerAnalyticsExportRun.FORMAT_CSV,
			status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
			error_message="failed marker",
		)

		response = self.client.get(f"{reverse('task-manager-admin:index')}?active_tab=ops-metrics&export_status=failed")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "failed marker")
		self.assertNotContains(response, "success marker")

	def test_non_staff_cannot_download_operational_analytics_exports(self):
		non_admin_user = get_user_model().objects.create_user(
			username="nonadmin@example.com",
			email="nonadmin@example.com",
			password="testpass123",
		)
		self.client.force_login(non_admin_user)
		csv_response = self.client.get(reverse("polish:task-manager:export-analytics-csv"))
		self.assertEqual(csv_response.status_code, 302)
		pdf_response = self.client.get(reverse("polish:task-manager:export-analytics-pdf"))
		self.assertEqual(pdf_response.status_code, 302)

	def test_create_assignment_under_task_manager_namespace(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.post(
			reverse("polish:task-manager:create-assignment"),
			{"title": "Engineered Assignment", "assignment_type": "twelve_point", "active_tab": "create"},
		)
		self.assertEqual(response.status_code, 302)
		self.assertIn("active_tab=create", response["Location"])
		self.assertTrue(TaskAssignment.objects.filter(title="Engineered Assignment").exists())

	def test_perpetual_assignment_requires_premium_subscription(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		response = self.client.post(
			reverse("polish:task-manager:create-assignment"),
			{"title": "Blocked Perpetual", "assignment_type": "perpetual", "active_tab": "create"},
		)
		self.assertEqual(response.status_code, 302)
		self.assertFalse(TaskAssignment.objects.filter(title="Blocked Perpetual").exists())

		architects, _ = Group.objects.get_or_create(name="architects")
		architects.user_set.add(self.user)
		self.user.subscription_tier = self.user.SUBSCRIPTION_PREMIUM_PRO
		self.user.save(update_fields=["subscription_tier"])
		allowed_response = self.client.post(
			reverse("polish:task-manager:create-assignment"),
			{"title": "Allowed Perpetual", "assignment_type": "perpetual", "active_tab": "create"},
		)
		self.assertEqual(allowed_response.status_code, 302)
		self.assertTrue(TaskAssignment.objects.filter(title="Allowed Perpetual").exists())

	def test_attach_and_advance_workflow_item(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Advancement Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		attach_response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{"objective_text": "Validate supplier outreach objective", "active_tab": "attach"},
		)
		self.assertEqual(attach_response.status_code, 302)
		self.assertIn("active_tab=attach", attach_response["Location"])
		item = TaskWorkflowItem.objects.get(assignment=assignment)

		advance_response = self.client.post(
			reverse("polish:task-manager:item-actions", args=[item.id]),
			{"action": "advance", "steps": "1", "active_tab": "item"},
		)
		self.assertEqual(advance_response.status_code, 302)
		self.assertIn("active_tab=item", advance_response["Location"])
		item.refresh_from_db()
		self.assertEqual(item.current_step_index, 1)
		self.assertEqual(item.current_compartment, "B")

	def test_attach_file_to_assignment(self):
		from polish.task_manager.attachment_security import AttachmentScanResult

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Attachment Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		with patch("polish.views.scan_uploaded_attachment") as mock_scan_uploaded_attachment:
			mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
				is_clean=True,
				status="clean",
				notes="simulated clean",
				sha256="abc",
			)
			response = self.client.post(
				reverse("polish:task-manager:attach-item", args=[assignment.id]),
				{
					"active_tab": "attach",
					"attachment_label": "Brief",
					"attachment_file": uploaded,
				},
			)
		self.assertEqual(response.status_code, 302)
		self.assertIn("active_tab=attach", response["Location"])
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 1)

	def test_attach_file_respects_user_storage_quota(self):
		from polish.task_manager.attachment_security import AttachmentScanResult

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Quota Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		TaskAssignmentAttachment.objects.create(
			assignment=assignment,
			uploaded_by=self.user,
			label="Existing",
			file=SimpleUploadedFile("existing.txt", b"x", content_type="text/plain"),
			file_size_bytes=self.user.get_storage_quota_bytes(),
			file_sha256="abc",
			scan_status="clean",
			scan_notes="seed",
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		with patch("polish.views.scan_uploaded_attachment") as mock_scan_uploaded_attachment:
			mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
				is_clean=True,
				status="clean",
				notes="simulated clean",
				sha256="abc",
			)
			response = self.client.post(
				reverse("polish:task-manager:attach-item", args=[assignment.id]),
				{
					"active_tab": "attach",
					"attachment_label": "Brief",
					"attachment_file": uploaded,
				},
			)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 1)

	def test_reject_attachment_with_unsupported_file_type(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Attachment Validation",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("script.exe", b"binary", content_type="application/octet-stream")
		response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"attachment_label": "Bad file",
				"attachment_file": uploaded,
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 0)


class QuarantineAdminWorkflowTests(TestCase):
	def setUp(self):
		self.admin_user = get_user_model().objects.create_user(
			username="admin-reviewer",
			email="admin-reviewer@example.com",
			password="testpass123",
			is_staff=True,
			is_superuser=True,
		)
		self.user = get_user_model().objects.create_user(
			username="engineer@example.com",
			email="engineer@example.com",
			password="testpass123",
			first_name="Engineer",
			last_name="User",
		)
		group, _ = Group.objects.get_or_create(name="engineers")
		group.user_set.add(self.user)
		polish_admin_group, _ = Group.objects.get_or_create(name="polish_admin")
		polish_admin_group.user_set.add(self.user)
		self.assignment = TaskAssignment.objects.create(
			title="Quarantine Test",
			assignment_type="linear",
			created_by=self.admin_user,
			assigned_to=self.admin_user,
		)
		self.site = AdminSite()
		self.admin_obj = TaskAttachmentQuarantineAdmin(TaskAttachmentQuarantine, self.site)
		self.request_factory = RequestFactory()

	def _make_request(self):
		request = self.request_factory.post("/admin/polish/taskattachmentquarantine/")
		request.user = self.admin_user
		request.session = self.client.session
		setattr(request, "_messages", FallbackStorage(request))
		return request

	def _make_quarantine(self, name="blocked.txt"):
		return TaskAttachmentQuarantine.objects.create(
			assignment=self.assignment,
			uploaded_by=self.admin_user,
			original_filename=name,
			label="Blocked",
			content_type="text/plain",
			file_size_bytes=10,
			file=SimpleUploadedFile(name, b"blocked", content_type="text/plain"),
			scan_status="flagged",
			reason="blocked for test",
		)

	def test_admin_approve_quarantine_action_releases_attachment_and_logs(self):
		item = self._make_quarantine("approve.txt")
		request = self._make_request()

		self.admin_obj.approve_quarantine_items(request, TaskAttachmentQuarantine.objects.filter(pk=item.pk))

		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=self.assignment).count(), 1)
		self.assertEqual(TaskAttachmentQuarantine.objects.filter(pk=item.pk).count(), 0)
		self.assertEqual(TaskAttachmentAuditLog.objects.filter(event_type="review_approved").count(), 1)

	@patch("polish.admin.scan_uploaded_attachment")
	def test_admin_rescan_quarantine_action_updates_status_and_logs(self, mock_scan):
		from polish.task_manager.attachment_security import AttachmentScanResult

		item = self._make_quarantine("rescan.txt")
		request = self._make_request()
		mock_scan.return_value = AttachmentScanResult(is_clean=False, status="flagged", notes="still blocked", sha256="abc")

		self.admin_obj.rescan_quarantine_items(request, TaskAttachmentQuarantine.objects.filter(pk=item.pk))

		item.refresh_from_db()
		self.assertEqual(item.review_status, item.REVIEW_RESCANNED)
		self.assertEqual(item.scan_status, "flagged")
		self.assertEqual(TaskAttachmentAuditLog.objects.filter(event_type="review_rescanned").count(), 1)

	def test_admin_delete_quarantine_action_removes_item_and_logs(self):
		item = self._make_quarantine("delete.txt")
		request = self._make_request()

		self.admin_obj.delete_quarantine_items(request, TaskAttachmentQuarantine.objects.filter(pk=item.pk))

		self.assertEqual(TaskAttachmentQuarantine.objects.filter(pk=item.pk).count(), 0)
		self.assertEqual(TaskAttachmentAuditLog.objects.filter(event_type="review_deleted").count(), 1)

	def test_quarantine_tab_renders_selected_detail(self):
		item = self._make_quarantine("detail.txt")
		self.client.force_login(self.admin_user)
		response = self.client.get(
			f"{reverse('task-manager-admin:index')}?active_tab=quarantine&quarantine_id={item.id}"
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Quarantine Review")
		self.assertContains(response, "detail.txt")

	def test_dedicated_quarantine_view_supports_filters_and_pagination(self):
		for index in range(50):
			item = self._make_quarantine(f"queue-{index:02d}.txt")
			if index % 3 == 0:
				item.review_status = item.REVIEW_RESCANNED
				item.save(update_fields=["review_status"])

		self.client.force_login(self.admin_user)
		response = self.client.get(
			reverse("polish:task-manager:quarantine-list"),
			{"review_status": "pending", "sort": "name_az", "page": 1},
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Quarantine Workflow")
		self.assertContains(response, "Active Filters")
		self.assertContains(response, "Active Constraints")
		self.assertContains(response, "Review: pending")
		self.assertContains(response, "Sort: name_az")
		self.assertContains(response, "Clear All")
		self.assertContains(response, "?sort=name_az")
		self.assertContains(response, "?review_status=pending")
		self.assertContains(response, "Page 1 of")

		page_two_response = self.client.get(
			reverse("polish:task-manager:quarantine-list"),
			{"review_status": "pending", "sort": "name_az", "page": 2},
		)
		self.assertEqual(page_two_response.status_code, 200)
		self.assertContains(page_two_response, "Page 2 of")

	def test_quarantine_action_respects_return_to_path(self):
		item = self._make_quarantine("return-to.txt")
		self.client.force_login(self.admin_user)
		return_to = f"{reverse('polish:task-manager:quarantine-list')}?review_status=pending"
		response = self.client.post(
			reverse("polish:task-manager:quarantine-actions", args=[item.id]),
			{"action": "rescan", "return_to": return_to},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], return_to)


	def test_staff_can_approve_quarantine_from_task_manager_action_view(self):
		item = self._make_quarantine("view-approve.txt")
		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse("polish:task-manager:quarantine-actions", args=[item.id]),
			{"active_tab": "quarantine", "action": "approve", "review_notes": "Approved from UI"},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAttachmentQuarantine.objects.filter(pk=item.pk).count(), 0)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=self.assignment).count(), 1)
		self.assertEqual(TaskAttachmentAuditLog.objects.filter(event_type="review_approved").count(), 1)

	def test_non_staff_cannot_execute_quarantine_review_action(self):
		item = self._make_quarantine("blocked-action.txt")
		non_admin_user = get_user_model().objects.create_user(
			username="review-blocked@example.com",
			email="review-blocked@example.com",
			password="testpass123",
		)
		self.client.force_login(non_admin_user)
		response = self.client.post(
			reverse("polish:task-manager:quarantine-actions", args=[item.id]),
			{"active_tab": "quarantine", "action": "delete"},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAttachmentQuarantine.objects.filter(pk=item.pk).count(), 1)

	def test_remove_attachment_from_assignment(self):
		from polish.task_manager.attachment_security import AttachmentScanResult

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Attachment Removal",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		with patch("polish.views.scan_uploaded_attachment") as mock_scan_uploaded_attachment:
			mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
				is_clean=True,
				status="clean",
				notes="simulated clean",
				sha256="abc",
			)
			create_response = self.client.post(
				reverse("polish:task-manager:attach-item", args=[assignment.id]),
				{
					"active_tab": "attach",
					"attachment_label": "Brief",
					"attachment_file": uploaded,
				},
			)
		self.assertEqual(create_response.status_code, 302)
		attachment = TaskAssignmentAttachment.objects.get(assignment=assignment)

		delete_response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"action": "remove_attachment",
				"attachment_id": str(attachment.id),
			},
		)
		self.assertEqual(delete_response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 0)

	def test_download_attachment_increments_counter(self):
		from polish.task_manager.attachment_security import AttachmentScanResult

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Attachment Download Counter",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		with patch("polish.views.scan_uploaded_attachment") as mock_scan_uploaded_attachment:
			mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
				is_clean=True,
				status="clean",
				notes="simulated clean",
				sha256="abc",
			)
			create_response = self.client.post(
				reverse("polish:task-manager:attach-item", args=[assignment.id]),
				{
					"active_tab": "attach",
					"attachment_label": "Brief",
					"attachment_file": uploaded,
				},
			)
		self.assertEqual(create_response.status_code, 302)
		attachment = TaskAssignmentAttachment.objects.get(assignment=assignment)

		download_response = self.client.get(
			reverse("polish:task-manager:download-attachment", args=[attachment.id])
		)
		self.assertEqual(download_response.status_code, 200)
		attachment.refresh_from_db()
		self.assertEqual(attachment.download_count, 1)

	def test_complete_assignment_captures_notes_and_report_is_downloadable(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Report Assignment",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)
		attach_response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"objective_text": "Finalize completion report objective",
			},
		)
		self.assertEqual(attach_response.status_code, 302)

		complete_response = self.client.post(
			reverse("polish:task-manager:assignment-actions", args=[assignment.id]),
			{
				"action": "complete",
				"active_tab": "assignment",
				"completion_notes": "Finished with verification",
			},
		)
		self.assertEqual(complete_response.status_code, 302)
		assignment.refresh_from_db()
		self.assertTrue(assignment.is_closed)
		self.assertEqual(assignment.completion_notes, "Finished with verification")
		self.assertIsNotNone(assignment.completed_at)

		report_response = self.client.get(
			reverse("polish:task-manager:assignment-report", args=[assignment.id])
		)
		self.assertEqual(report_response.status_code, 200)
		self.assertIn("application/pdf", report_response["Content-Type"])

	def test_invalid_mime_upload_is_quarantined_and_audited(self):
		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="MIME Guard",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("fake.pdf", b"pretend", content_type="application/x-msdownload")
		response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"attachment_label": "Suspicious",
				"attachment_file": uploaded,
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 0)
		self.assertEqual(TaskAttachmentQuarantine.objects.filter(assignment=assignment).count(), 1)
		self.assertEqual(TaskAttachmentAuditLog.objects.filter(assignment=assignment, event_type="blocked").count(), 1)

	def test_download_attachment_requires_allowed_role(self):
		outsider = get_user_model().objects.create_user(
			username="outsider@example.com",
			email="outsider@example.com",
			password="testpass123",
		)
		assignment = TaskAssignment.objects.create(
			title="Restricted Download",
			assignment_type="linear",
			created_by=outsider,
			assigned_to=outsider,
		)

		attachment = TaskAssignmentAttachment.objects.create(
			assignment=assignment,
			uploaded_by=outsider,
			label="Brief",
			file=SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain"),
			file_size_bytes=len(b"assignment brief"),
			file_sha256="abc",
			scan_status="clean",
			scan_notes="seeded for access test",
		)

		self.client.login(username="outsider@example.com", password="testpass123")

		download_response = self.client.get(
			reverse("polish:task-manager:download-attachment", args=[attachment.id])
		)
		self.assertEqual(download_response.status_code, 302)
		attachment.refresh_from_db()
		self.assertEqual(attachment.download_count, 0)

	@patch("polish.views.scan_uploaded_attachment")
	def test_reject_attachment_when_scan_flags_file(self, mock_scan_uploaded_attachment):
		from polish.task_manager.attachment_security import AttachmentScanResult

		mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
			is_clean=False,
			status="flagged",
			notes="simulated malware",
			sha256="abc",
		)

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Flagged Upload",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"attachment_label": "Brief",
				"attachment_file": uploaded,
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 0)


class TaskManagerAnalyticsExportCommandTests(TestCase):
	def setUp(self):
		self.staff_user = get_user_model().objects.create_user(
			username="staff-export",
			email="staff-export@example.com",
			password="testpass123",
			is_staff=True,
		)
		self.user = get_user_model().objects.create_user(
			username="engineer@example.com",
			email="engineer@example.com",
			password="testpass123",
		)

	def test_export_command_generates_csv_and_pdf_files(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			call_command(
				"export_task_manager_analytics",
				"--email",
				self.staff_user.email,
				"--output-dir",
				tmpdir,
			)
			files = list(Path(tmpdir).iterdir())
			self.assertTrue(any(path.suffix == ".csv" for path in files))
			self.assertTrue(any(path.suffix == ".pdf" for path in files))
			runs = TaskManagerAnalyticsExportRun.objects.filter(
				target_user=self.staff_user,
				trigger_source=TaskManagerAnalyticsExportRun.SOURCE_COMMAND,
			)
			self.assertEqual(runs.count(), 1)

	@patch("polish.management.commands.export_task_manager_analytics._build_operational_metrics_pdf")
	def test_export_command_records_failed_history_row(self, mock_build_operational_metrics_pdf):
		mock_build_operational_metrics_pdf.side_effect = RuntimeError("simulated command pdf failure")
		with tempfile.TemporaryDirectory() as tmpdir:
			with self.assertRaises(CommandError):
				call_command(
					"export_task_manager_analytics",
					"--email",
					self.staff_user.email,
					"--output-dir",
					tmpdir,
				)

		failed_run = TaskManagerAnalyticsExportRun.objects.filter(
			target_user=self.staff_user,
			trigger_source=TaskManagerAnalyticsExportRun.SOURCE_COMMAND,
			status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
		).first()
		self.assertIsNotNone(failed_run)
		self.assertIn("simulated command pdf failure", failed_run.error_message)

	@patch("polish.views.scan_uploaded_attachment")
	def test_reject_attachment_when_scan_errors(self, mock_scan_uploaded_attachment):
		from polish.task_manager.attachment_security import AttachmentScanResult

		mock_scan_uploaded_attachment.return_value = AttachmentScanResult(
			is_clean=False,
			status="error",
			notes="clamscan unavailable",
			sha256="abc",
		)

		self.client.login(username="engineer@example.com", password="testpass123")
		assignment = TaskAssignment.objects.create(
			title="Scan Error Upload",
			assignment_type="linear",
			created_by=self.user,
			assigned_to=self.user,
		)

		uploaded = SimpleUploadedFile("brief.txt", b"assignment brief", content_type="text/plain")
		response = self.client.post(
			reverse("polish:task-manager:attach-item", args=[assignment.id]),
			{
				"active_tab": "attach",
				"attachment_label": "Brief",
				"attachment_file": uploaded,
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(TaskAssignmentAttachment.objects.filter(assignment=assignment).count(), 0)


class PolishAdminRoleCommandTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="polish-role-user",
			email="polish-role-user@example.com",
			password="testpass123",
		)

	def test_grant_polish_admin_by_email_without_staff(self):
		stdout = StringIO()
		call_command("grant_polish_admin", "--email", self.user.email, stdout=stdout)

		self.user.refresh_from_db()
		self.assertTrue(self.user.groups.filter(name="polish_admin").exists())
		self.assertFalse(self.user.is_staff)

	def test_revoke_polish_admin(self):
		group, _ = Group.objects.get_or_create(name="polish_admin")
		group.user_set.add(self.user)

		stdout = StringIO()
		call_command("grant_polish_admin", "--email", self.user.email, "--revoke", stdout=stdout)

		self.user.refresh_from_db()
		self.assertFalse(self.user.groups.filter(name="polish_admin").exists())

	def test_command_requires_selector(self):
		with self.assertRaises(CommandError):
			call_command("grant_polish_admin")
