from django.test import TestCase
from django.urls import reverse

from .constants import DOMAIN_COMPARTMENT_DEFINITIONS
from .models import DomainProfile
from users.models import User


class DomainProfileTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='domainuser@example.com',
			username='domainuser',
			name='Domain User',
			password='testpass123',
		)

	def test_domain_index_requires_login(self):
		response = self.client.get(reverse('domain:index'))
		self.assertEqual(response.status_code, 302)

	def test_domain_index_loads_for_authenticated_user(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:index'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Personal Domain')
		self.assertContains(response, 'Edit domain')
		self.assertContains(response, 'Persuasive')
		self.assertContains(response, 'Domain Boards')
		self.assertContains(response, 'Personal Corporation')
		self.assertContains(response, 'Personal Museum')
		self.assertContains(response, 'Personal Garden')
		self.assertContains(response, 'Analyze')
		self.assertContains(response, 'Evaluate')

	def test_domain_edit_page_loads_for_authenticated_user(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:edit'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Rename your compartments')
		self.assertContains(response, 'Locked compartments')

	def test_domain_profile_can_be_renamed(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		payload = {
			'compartment_1_label': 'Custom Compartment One',
			'compartment_2_label': 'Custom Compartment Two',
			'compartment_3_label': 'Custom Compartment Three',
			'compartment_4_label': 'Custom Compartment Four',
			'compartment_5_label': 'Custom Compartment Five',
			'compartment_8_label': 'Custom Compartment Eight',
			'compartment_9_label': 'Custom Compartment Nine',
			'compartment_10_label': 'Custom Compartment Ten',
			'compartment_11_label': 'Custom Compartment Eleven',
			'compartment_12_label': 'Custom Compartment Twelve',
			'board_corporation_label': 'Personal Corporation Studio',
			'board_museum_label': 'Personal Museum Gallery',
			'board_garden_label': 'Personal Garden Workspace',
		}
		response = self.client.post(reverse('domain:edit'), payload, follow=True)
		self.assertEqual(response.status_code, 200)
		profile = DomainProfile.objects.get(user=self.user)
		self.assertEqual(profile.compartment_1_label, 'Custom Compartment One')
		self.assertEqual(profile.compartment_6_label, 'Analyze')
		self.assertEqual(profile.compartment_7_label, 'Evaluate')
		self.assertEqual(profile.board_corporation_label, 'Personal Corporation Studio')
		self.assertContains(response, 'Custom Compartment One')
		self.assertContains(response, 'Personal Corporation Studio')

	def test_domain_profile_rejects_short_labels(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		payload = {
			'compartment_1_label': 'Too Short',
			'board_corporation_label': 'Short Name',
		}
		response = self.client.post(reverse('domain:edit'), payload)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Use at least 12 characters')
		self.assertContains(response, 'Use at least 16 characters')

	def test_domain_cell_detail_loads(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:cell_detail', kwargs={'slug': 'persuasive'}))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Technology')
		self.assertContains(response, '8 pm')

	def test_domain_tr_cell_shows_12am(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:cell_detail', kwargs={'slug': 'tr'}))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '12 am')

	def test_domain_cell_detail_404_for_unknown_slug(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:cell_detail', kwargs={'slug': 'unknown-cell'}))
		self.assertEqual(response.status_code, 404)
