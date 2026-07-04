from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group

from users.models import User


class HomeViewTests(TestCase):
	def test_home_page_loads(self):
		response = self.client.get(reverse("index"))
		self.assertEqual(response.status_code, 200)

	def test_slides_hub_loads(self):
		response = self.client.get(reverse("slides-hub"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Slides Hub")
		self.assertContains(response, "/slides/architecture/")
		self.assertContains(response, "/slides/executive/")
		self.assertContains(response, "/workflow/btsrl/")

	def test_architecture_slides_page_loads(self):
		response = self.client.get(reverse("architecture-slides"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Incubation Ecosystem")

	def test_btsrl_page_loads(self):
		response = self.client.get(reverse("btsrl"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "BaseTrue Square Root Lattice")
		self.assertContains(response, "4-Step Linear Phase")
		self.assertContains(response, "16,777,216")

	def test_executive_slides_requires_login(self):
		response = self.client.get(reverse("executive-slides"))
		self.assertEqual(response.status_code, 403)

	def test_executive_slides_blocks_non_staff_user(self):
		user = User.objects.create_user(
			email="member@example.com",
			username="member",
			name="Member User",
			password="testpass123",
		)
		self.client.force_login(user)

		response = self.client.get(reverse("executive-slides"))
		self.assertEqual(response.status_code, 403)

	def test_executive_slides_blocks_staff_without_group(self):
		user = User.objects.create_user(
			email="staff@example.com",
			username="staffmember",
			name="Staff User",
			password="testpass123",
			is_staff=True,
		)
		self.client.force_login(user)

		response = self.client.get(reverse("executive-slides"))
		self.assertEqual(response.status_code, 403)

	def test_executive_slides_allows_user_with_access_group(self):
		group, _ = Group.objects.get_or_create(name="executive_slides_access")
		user = User.objects.create_user(
			email="exec@example.com",
			username="execmember",
			name="Exec User",
			password="testpass123",
		)
		user.groups.add(group)
		self.client.force_login(user)

		response = self.client.get(reverse("executive-slides"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Executive Strategy Deck")
