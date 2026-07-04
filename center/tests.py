from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from polish.models import PolishReminderPreference, PolishTask

from .models import CorporationItem


class CenterBoardsTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="centeruser@example.com",
			email="centeruser@example.com",
			password="testpass123",
			first_name="Center",
			last_name="User",
		)

	def test_center_index_links_to_board_pages(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.get(reverse("center:index"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, reverse("center:corporation_admin"))
		self.assertContains(response, reverse("center:museum_social"))
		self.assertContains(response, reverse("center:garden_board"))

	def test_corporation_admin_requires_login(self):
		response = self.client.get(reverse("center:corporation_admin"))
		self.assertEqual(response.status_code, 302)

	def test_corporation_admin_loads_for_authenticated_user(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.get(reverse("center:corporation_admin"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Corporation Admin")
		self.assertContains(response, "Task + Reminder (From Corporation)")

	def test_corporation_admin_adds_polish_task(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "add_polish_task",
				"title": "Corporate task",
				"details": "Created from corporation page",
				"due_date": "2026-07-20",
			},
		)
		self.assertEqual(response.status_code, 302)
		task = PolishTask.objects.get(title="Corporate task")
		self.assertEqual(task.user, self.user)

	def test_corporation_admin_completes_polish_task(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		task = PolishTask.objects.create(user=self.user, title="Complete me")
		response = self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "complete_polish_task",
				"task_id": str(task.id),
			},
		)
		self.assertEqual(response.status_code, 302)
		task.refresh_from_db()
		self.assertTrue(task.is_completed)

	def test_corporation_admin_updates_polish_reminder_preference(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "update_polish_reminder_preference",
				"enabled": "on",
			},
		)
		self.assertEqual(response.status_code, 302)
		preference = PolishReminderPreference.objects.get(user=self.user)
		self.assertTrue(preference.enabled)

	def test_museum_social_loads_for_authenticated_user(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.get(reverse("center:museum_social"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Museum Social")

	def test_garden_board_loads_for_authenticated_user(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.get(reverse("center:garden_board"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Garden Board")

	def test_corporation_create_item(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		response = self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "create",
				"title": "Summer Exhibit Campaign",
				"description": "Launch plan for summer campaign.",
				"item_type": CorporationItem.TYPE_CAMPAIGN,
				"priority": CorporationItem.PRIORITY_HIGH,
				"due_date": "2026-07-01",
			},
		)
		self.assertEqual(response.status_code, 302)
		item = CorporationItem.objects.get(title="Summer Exhibit Campaign")
		self.assertEqual(item.owner, self.user)
		self.assertEqual(item.status, CorporationItem.STATUS_DRAFT)

	def test_corporation_transition_to_approved_sets_timestamp(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		item = CorporationItem.objects.create(
			owner=self.user,
			title="Press Outreach",
			item_type=CorporationItem.TYPE_GENERAL,
		)

		self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "transition",
				"item_id": str(item.id),
				"next_status": CorporationItem.STATUS_REVIEW,
			},
		)
		item.refresh_from_db()
		self.assertEqual(item.status, CorporationItem.STATUS_REVIEW)

		self.client.post(
			reverse("center:corporation_admin"),
			{
				"action": "transition",
				"item_id": str(item.id),
				"next_status": CorporationItem.STATUS_APPROVED,
			},
		)
		item.refresh_from_db()
		self.assertEqual(item.status, CorporationItem.STATUS_APPROVED)
		self.assertIsNotNone(item.approved_at)

	def test_museum_mark_posted_moves_approved_item_to_posted(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		item = CorporationItem.objects.create(
			owner=self.user,
			title="Feature Reel",
			item_type=CorporationItem.TYPE_CAMPAIGN,
			status=CorporationItem.STATUS_APPROVED,
		)

		response = self.client.post(
			reverse("center:museum_social"),
			{"item_id": str(item.id)},
		)
		self.assertEqual(response.status_code, 302)
		item.refresh_from_db()
		self.assertEqual(item.status, CorporationItem.STATUS_POSTED)
		self.assertEqual(item.work_status, CorporationItem.WORK_STATUS_TODO)

	def test_garden_progression_from_todo_to_done(self):
		self.client.login(username="centeruser@example.com", password="testpass123")
		item = CorporationItem.objects.create(
			owner=self.user,
			title="Launch Story Thread",
			item_type=CorporationItem.TYPE_CAMPAIGN,
			status=CorporationItem.STATUS_POSTED,
			work_status=CorporationItem.WORK_STATUS_TODO,
		)

		response = self.client.post(
			reverse("center:garden_board"),
			{
				"item_id": str(item.id),
				"next_work_status": CorporationItem.WORK_STATUS_IN_PROGRESS,
			},
		)
		self.assertEqual(response.status_code, 302)
		item.refresh_from_db()
		self.assertEqual(item.work_status, CorporationItem.WORK_STATUS_IN_PROGRESS)
		self.assertIsNotNone(item.work_started_at)

		response = self.client.post(
			reverse("center:garden_board"),
			{
				"item_id": str(item.id),
				"next_work_status": CorporationItem.WORK_STATUS_DONE,
			},
		)
		self.assertEqual(response.status_code, 302)
		item.refresh_from_db()
		self.assertEqual(item.work_status, CorporationItem.WORK_STATUS_DONE)
		self.assertIsNotNone(item.work_completed_at)
