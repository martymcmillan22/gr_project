from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import ForumPost


class ForumPagesTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="forum-user",
			email="forum@example.com",
			password="pass1234",
		)

	def test_global_forum_is_public(self):
		response = self.client.get(reverse("forums:global"))
		self.assertEqual(response.status_code, 200)

	def test_forum_access_pages_are_shareable(self):
		self.assertEqual(self.client.get(reverse("forums:access", kwargs={"forum_key": "city"})).status_code, 200)
		self.assertEqual(self.client.get(reverse("forums:access", kwargs={"forum_key": "state"})).status_code, 200)
		self.assertEqual(self.client.get(reverse("forums:access", kwargs={"forum_key": "national"})).status_code, 200)
		self.assertEqual(self.client.get(reverse("forums:access", kwargs={"forum_key": "global"})).status_code, 200)

	def test_forum_access_page_points_to_login_for_protected_forum(self):
		response = self.client.get(reverse("forums:access", kwargs={"forum_key": "city"}))
		self.assertContains(response, reverse("login") + "?next=" + reverse("forums:city"))

	def test_city_state_national_forums_require_login(self):
		self.assertEqual(self.client.get(reverse("forums:city")).status_code, 302)
		self.assertEqual(self.client.get(reverse("forums:state")).status_code, 302)
		self.assertEqual(self.client.get(reverse("forums:national")).status_code, 302)

	def test_city_state_national_forums_load_for_authenticated_user(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get(reverse("forums:city")).status_code, 200)
		self.assertEqual(self.client.get(reverse("forums:state")).status_code, 200)
		self.assertEqual(self.client.get(reverse("forums:national")).status_code, 200)

	def test_authenticated_user_can_create_city_forum_post(self):
		self.client.force_login(self.user)
		response = self.client.post(reverse("forums:city"), {"title": "Street update", "body": "Local planning note."})
		self.assertEqual(response.status_code, 302)
		post = ForumPost.objects.get()
		self.assertEqual(post.forum_type, ForumPost.FORUM_CITY)
		self.assertEqual(post.author, self.user)

	def test_global_forum_shows_posts_publicly(self):
		ForumPost.objects.create(
			forum_type=ForumPost.FORUM_GLOBAL,
			author=self.user,
			title="World brief",
			body="Global coordination note.",
		)
		response = self.client.get(reverse("forums:global"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "World brief")

	def test_anonymous_global_post_redirects_to_login(self):
		response = self.client.post(reverse("forums:global"), {"title": "Anon", "body": "Should not post."})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(ForumPost.objects.count(), 0)
