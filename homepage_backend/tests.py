from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import HomepageAction, HomepageBackendItem, HomepageFlow, HomepagePreference, HomepageTask


class HomepageBackendItemApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="homepage-owner",
            email="homepage@example.com",
            password="testpass123",
            name="HomepageBackendItem Owner",
        )
        self.other = User.objects.create_user(
            username="homepage-other",
            email="homepage-other@example.com",
            password="testpass123",
            name="HomepageBackendItem Other",
        )
        self.client.force_authenticate(self.user)

    def test_create_assigns_owner(self):
        url = reverse("homepage-items-list")
        response = self.client.post(url, {"title": "Sample", "summary": "Body"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = HomepageBackendItem.objects.get(id=response.data["id"])
        self.assertEqual(item.owner_id, self.user.id)

    def test_non_owner_cannot_read_item(self):
        item = HomepageBackendItem.objects.create(owner=self.user, title="A")
        self.client.force_authenticate(self.other)

        url = reverse("homepage-items-detail", args=[item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_overview_returns_flow_tasks_and_settings(self):
        HomepageFlow.objects.create(owner=self.user, name="Daily Flow", status="active", progress=42)
        HomepageTask.objects.create(owner=self.user, title="Review Notes", description="Check today's flow")
        HomepagePreference.objects.create(owner=self.user, notifications=True, dark_mode=False, view_state={"active_panel": "rr_dashboard"})

        url = reverse("homepage-overview")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["flow"]["name"], "Daily Flow")
        self.assertEqual(len(response.data["tasks"]), 1)
        self.assertEqual(response.data["settings"]["notifications"], True)
        self.assertEqual(response.data["settings"]["view_state"]["active_panel"], "rr_dashboard")

    def test_preferences_view_state_round_trip(self):
        url = reverse("homepage-preferences-list")
        create_response = self.client.post(
            url,
            {"notifications": True, "dark_mode": False, "view_state": {"rr": {"phase_filter": "SEED"}}},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        preference_id = create_response.data["id"]
        patch_response = self.client.patch(
            reverse("homepage-preferences-detail", args=[preference_id]),
            {"view_state": {"rr": {"phase_filter": "PROJECT", "selected_lane": 4}}},
            format="json",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["view_state"]["rr"]["phase_filter"], "PROJECT")
        self.assertEqual(patch_response.data["view_state"]["rr"]["selected_lane"], 4)

    def test_create_action_writes_homepage_action(self):
        url = reverse("homepage-actions-list")
        response = self.client.post(url, {"label": "Start Flow"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HomepageAction.objects.count(), 1)

    def test_presentation_slides_endpoint_returns_manifest_shape(self):
        url = reverse("homepage-presentation-slides")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("generated_at", response.data)
        self.assertIn("slides", response.data)
        self.assertIn("manifest_path", response.data)
