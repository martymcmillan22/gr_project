from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .markdown_parser import StoryEntry
from .models import StorySession


class StoryDashboardOwnershipTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin = self.user_model.objects.create_superuser(
            email='admin@example.com',
            username='adminuser',
            name='Admin User',
            password='testpass123',
        )
        self.owner = self.user_model.objects.create_user(
            email='owner@example.com',
            username='owner',
            name='Owner User',
            password='testpass123',
        )
        self.other_user = self.user_model.objects.create_user(
            email='other@example.com',
            username='other',
            name='Other User',
            password='testpass123',
        )

    @patch('storytelling_dashboard.views.StoryMarkdownParser.load_all_stories')
    def test_dashboard_only_shows_owned_or_admin_visible_stories(self, load_all_stories):
        load_all_stories.return_value = [
            StoryEntry(1, 'Owned Story', 'complete'),
            StoryEntry(2, 'Other Story', 'pending'),
        ]

        StorySession.objects.create(
            entry_id=1,
            title='Owned Story',
            status='complete',
            format='movie',
            progress=100,
            owner=self.owner,
        )
        StorySession.objects.create(
            entry_id=2,
            title='Other Story',
            status='pending',
            format='movie',
            progress=0,
            owner=self.other_user,
        )

        self.client.force_login(self.owner)
        response = self.client.get(reverse('storytelling_dashboard:dashboard'))

        self.assertContains(response, 'Owned Story')
        self.assertNotContains(response, 'Other Story')

        self.client.force_login(self.other_user)
        response = self.client.get(reverse('storytelling_dashboard:dashboard'))

        self.assertContains(response, 'Other Story')
        self.assertNotContains(response, 'Owned Story')

        self.client.force_login(self.admin)
        response = self.client.get(reverse('storytelling_dashboard:dashboard'))

        self.assertContains(response, 'Owned Story')
        self.assertContains(response, 'Other Story')

    @patch('storytelling_dashboard.views.StoryMarkdownParser.create_entry')
    @patch('storytelling_dashboard.views.StoryMarkdownParser.load_all_stories')
    def test_create_outline_redirects_back_to_dashboard(self, load_all_stories, create_entry):
        load_all_stories.return_value = [StoryEntry(17, 'Existing Story', 'complete')]
        create_entry.return_value = True

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('storytelling_dashboard:story_create'),
            data={'title': 'New Story Outline', 'format': 'movie'},
        )

        self.assertRedirects(response, reverse('storytelling_dashboard:dashboard'))
        self.assertTrue(StorySession.objects.filter(title='New Story Outline', owner=self.owner).exists())