from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import CreativeIdea
from users.models import User
from polish.models import PolishTask, PolishReminderPreference


class TwistTokenViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='tokenuser@example.com',
			username='tokenuser',
			name='Token User',
			password='testpass123',
		)

	def test_token_page_requires_login(self):
		response = self.client.get(reverse('twist-token'))
		self.assertEqual(response.status_code, 302)

	def test_token_page_shows_users_token(self):
		self.client.login(username='tokenuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-token'))

		self.assertEqual(response.status_code, 200)
		token = Token.objects.get(user=self.user)
		self.assertContains(response, token.key)


class TwistEntryViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='entryuser@example.com',
			username='entryuser',
			name='Entry User',
			password='testpass123',
		)
		self.other_user = User.objects.create_user(
			email='otherentry@example.com',
			username='otherentry',
			name='Other Entry',
			password='testpass123',
		)

	def test_entry_page_prompts_guests_to_log_in(self):
		response = self.client.get(reverse('twist-entry'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Please log in first to save your ideas.')

	def test_entry_page_shows_only_authenticated_users_ideas(self):
		CreativeIdea.objects.create(user=self.user, content='my saved idea', tags='music')
		CreativeIdea.objects.create(user=self.other_user, content='someone else idea')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Capture an idea')
		self.assertContains(response, 'my saved idea')
		self.assertContains(response, 'music')
		self.assertNotContains(response, 'someone else idea')

	def test_entry_page_post_saves_idea_for_logged_in_user(self):
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.post(
			reverse('twist-entry'),
			{'content': 'captured from web', 'tags': 'voice, note', 'status': 'SEED'},
		)

		self.assertEqual(response.status_code, 302)
		idea = CreativeIdea.objects.get(content='captured from web')
		self.assertEqual(idea.user, self.user)
		self.assertEqual(idea.tags, 'voice, note')
		self.assertEqual(idea.status, 'SEED')

	def test_entry_page_post_rejects_whitespace_content(self):
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.post(reverse('twist-entry'), {'content': '   '})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Content cannot be empty.')
		self.assertEqual(CreativeIdea.objects.count(), 0)

	def test_edit_page_shows_existing_idea_content(self):
		idea = CreativeIdea.objects.create(user=self.user, content='draft idea', tags='draft')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-idea-edit', kwargs={'pk': idea.pk}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'draft idea')
		self.assertContains(response, 'draft')

	def test_edit_post_updates_logged_in_users_idea(self):
		idea = CreativeIdea.objects.create(user=self.user, content='draft idea')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.post(
			reverse('twist-idea-edit', kwargs={'pk': idea.pk}),
			{'content': 'updated idea', 'tags': 'refined, shortlist', 'status': 'BUSINESS'},
		)

		self.assertEqual(response.status_code, 302)
		idea.refresh_from_db()
		self.assertEqual(idea.content, 'updated idea')
		self.assertEqual(idea.tags, 'refined, shortlist')
		self.assertEqual(idea.status, 'BUSINESS')

	def test_edit_cannot_access_other_users_idea(self):
		idea = CreativeIdea.objects.create(user=self.other_user, content='private idea')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-idea-edit', kwargs={'pk': idea.pk}))

		self.assertEqual(response.status_code, 404)

	def test_delete_post_removes_logged_in_users_idea(self):
		idea = CreativeIdea.objects.create(user=self.user, content='remove me')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.post(reverse('twist-idea-delete', kwargs={'pk': idea.pk}))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(CreativeIdea.objects.filter(pk=idea.pk).exists())

	def test_delete_cannot_remove_other_users_idea(self):
		idea = CreativeIdea.objects.create(user=self.other_user, content='private idea')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.post(reverse('twist-idea-delete', kwargs={'pk': idea.pk}))

		self.assertEqual(response.status_code, 404)
		self.assertTrue(CreativeIdea.objects.filter(pk=idea.pk).exists())

	def test_delete_page_shows_confirmation_details(self):
		idea = CreativeIdea.objects.create(user=self.user, content='delete me later', tags='cleanup')
		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-idea-delete', kwargs={'pk': idea.pk}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Delete idea')
		self.assertContains(response, 'delete me later')
		self.assertContains(response, 'cleanup')

	def test_entry_page_search_filters_by_content_and_tags(self):
		CreativeIdea.objects.create(user=self.user, content='record guitar loop', tags='music, audio')
		CreativeIdea.objects.create(user=self.user, content='draw landing page', tags='design')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'), {'q': 'music'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'record guitar loop')
		self.assertNotContains(response, 'draw landing page')

	def test_entry_page_search_filters_by_tag_or_text(self):
		CreativeIdea.objects.create(user=self.user, content='prototype dashboard', tags='analytics')
		CreativeIdea.objects.create(user=self.user, content='voice memo', tags='audio')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'), {'q': 'prototype'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'prototype dashboard')
		self.assertNotContains(response, 'voice memo')

	def test_entry_page_filters_by_status(self):
		CreativeIdea.objects.create(user=self.user, content='raw idea', status='RAW')
		CreativeIdea.objects.create(user=self.user, content='seed idea', status='SEED')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'), {'status': 'SEED'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'seed idea')
		self.assertNotContains(response, 'raw idea')

	def test_entry_page_shows_clickable_tag_chip(self):
		CreativeIdea.objects.create(user=self.user, content='record guitar loop', tags='music, audio')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '?q=music&status=all')

	def test_entry_page_pagination_shows_second_page(self):
		for i in range(9):
			CreativeIdea.objects.create(user=self.user, content=f'idea {i + 1}')

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'), {'page': 2})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Page 2 of 2')
		self.assertContains(response, 'idea 1')
		self.assertNotContains(response, 'idea 9')

	def test_entry_page_shows_polish_popup_when_opted_in_and_tasks_unfinished(self):
		PolishTask.objects.create(user=self.user, title='unfinished polish task')
		PolishReminderPreference.objects.create(user=self.user, enabled=True)

		self.client.login(username='entryuser@example.com', password='testpass123')
		response = self.client.get(reverse('twist-entry'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Polish Reminder')
		self.assertContains(response, 'unfinished task')

	def test_entry_page_polish_popup_only_once_per_day(self):
		PolishTask.objects.create(user=self.user, title='unfinished polish task')
		preference = PolishReminderPreference.objects.create(user=self.user, enabled=True)

		self.client.login(username='entryuser@example.com', password='testpass123')
		first_response = self.client.get(reverse('twist-entry'))
		self.assertContains(first_response, 'Polish Reminder')

		preference.refresh_from_db()
		self.assertIsNotNone(preference.last_reminded_on)

		second_response = self.client.get(reverse('twist-entry'))
		self.assertNotContains(second_response, 'Polish Reminder')


class CreativeIdeaAPITests(APITestCase):
	def setUp(self):
		self.user1 = User.objects.create_user(
			email='user1@example.com',
			username='user1',
			name='User One',
			password='testpass123',
		)
		self.user2 = User.objects.create_user(
			email='user2@example.com',
			username='user2',
			name='User Two',
			password='testpass123',
		)
		self.list_url = reverse('ideas-list')

	def test_list_requires_authentication(self):
		response = self.client.get(self.list_url)
		self.assertIn(
			response.status_code,
			(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
		)

	def test_list_returns_only_authenticated_users_ideas(self):
		CreativeIdea.objects.create(user=self.user1, content='mine')
		CreativeIdea.objects.create(user=self.user2, content='not mine')

		self.client.force_authenticate(user=self.user1)
		response = self.client.get(self.list_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('results', response.data)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['content'], 'mine')

	def test_list_includes_pagination_metadata(self):
		CreativeIdea.objects.create(user=self.user1, content='first')
		CreativeIdea.objects.create(user=self.user1, content='second')

		self.client.force_authenticate(user=self.user1)
		response = self.client.get(self.list_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('count', response.data)
		self.assertIn('next', response.data)
		self.assertIn('previous', response.data)
		self.assertIn('results', response.data)
		self.assertEqual(response.data['count'], 2)

	def test_create_assigns_authenticated_user(self):
		self.client.force_authenticate(user=self.user1)
		response = self.client.post(
			self.list_url,
			{'content': 'new idea', 'tags': 'brainstorm, quick', 'status': 'SEED'},
			format='json'
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = CreativeIdea.objects.get(id=response.data['id'])
		self.assertEqual(created.user, self.user1)
		self.assertEqual(created.content, 'new idea')
		self.assertEqual(created.tags, 'brainstorm, quick')
		self.assertEqual(created.status, 'SEED')

	def test_create_defaults_to_raw_status(self):
		self.client.force_authenticate(user=self.user1)
		response = self.client.post(self.list_url, {'content': 'status defaults'}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = CreativeIdea.objects.get(id=response.data['id'])
		self.assertEqual(created.status, 'RAW')

	def test_create_rejects_whitespace_content(self):
		self.client.force_authenticate(user=self.user1)
		response = self.client.post(self.list_url, {'content': '   '}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('content', response.data)

	def test_create_rejects_content_over_max_length(self):
		self.client.force_authenticate(user=self.user1)
		response = self.client.post(self.list_url, {'content': 'x' * 5001}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('content', response.data)

	def test_cannot_update_other_users_idea(self):
		other_idea = CreativeIdea.objects.create(user=self.user2, content='locked')
		detail_url = reverse('ideas-detail', kwargs={'pk': other_idea.pk})

		self.client.force_authenticate(user=self.user1)
		response = self.client.patch(detail_url, {'content': 'changed'}, format='json')

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		other_idea.refresh_from_db()
		self.assertEqual(other_idea.content, 'locked')

	def test_cannot_delete_other_users_idea(self):
		other_idea = CreativeIdea.objects.create(user=self.user2, content='locked')
		detail_url = reverse('ideas-detail', kwargs={'pk': other_idea.pk})

		self.client.force_authenticate(user=self.user1)
		response = self.client.delete(detail_url)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertTrue(CreativeIdea.objects.filter(pk=other_idea.pk).exists())
