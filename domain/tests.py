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
		self.assertContains(response, 'Personal Matters Policy')
		self.assertContains(response, 'Personal artifacts only')
		self.assertContains(response, 'Edit domain')
		self.assertContains(response, 'Persuasive')
		self.assertContains(response, 'Domain Boards')
		self.assertContains(response, 'Personal Corpor')
		self.assertContains(response, 'Personal Museum')
		self.assertContains(response, 'Personal Garden')
		self.assertContains(response, reverse('center:corporation_admin') + '?visibility=personal')
		self.assertContains(response, reverse('center:museum_social') + '?visibility=personal')
		self.assertContains(response, reverse('center:garden_board') + '?visibility=personal')
		self.assertContains(response, 'Analyze')
		self.assertContains(response, 'Evaluate')

	def test_domain_edit_page_loads_for_authenticated_user(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:edit'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Rename your compartments')
		self.assertContains(response, 'Locked compartments')
		self.assertContains(response, '16 for interfaces')

	def test_domain_profile_can_be_renamed(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		payload = {
			'compartment_1_label': 'Compartment Alpha Long',
			'compartment_2_label': 'Custom Compartment Two',
			'compartment_3_label': 'Custom Compartment Three',
			'compartment_4_label': 'Custom Compartment Four',
			'compartment_5_label': 'Custom Compartment Five',
			'compartment_8_label': 'Custom Compartment Eight',
			'compartment_9_label': 'Custom Compartment Nine',
			'compartment_10_label': 'Custom Compartment Ten',
			'compartment_11_label': 'Custom Compartment Eleven',
			'compartment_12_label': 'Custom Compartment Twelve',
			'board_corporation_label': 'Personal Corporation Studio Suite',
			'board_museum_label': 'Personal Museum Gallery',
			'board_garden_label': 'Personal Garden Workspace',
		}
		response = self.client.post(reverse('domain:edit'), payload, follow=True)
		self.assertEqual(response.status_code, 200)
		profile = DomainProfile.objects.get(user=self.user)
		self.assertEqual(profile.compartment_1_label, 'Compartment Alpha Long')
		self.assertEqual(profile.compartment_6_label, 'Analyze')
		self.assertEqual(profile.compartment_7_label, 'Evaluate')
		self.assertEqual(profile.board_corporation_label, 'Personal Corporation Studio Suite')

	def test_domain_profile_accepts_short_labels_and_keeps_full_values(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		payload = {
			'compartment_1_label': 'Home',
			'board_corporation_label': 'Studio',
		}
		response = self.client.post(reverse('domain:edit'), payload, follow=True)
		self.assertEqual(response.status_code, 200)
		profile = DomainProfile.objects.get(user=self.user)
		self.assertEqual(profile.compartment_1_label, 'Home')
		self.assertEqual(profile.board_corporation_label, 'Studio')
		self.assertNotContains(response, 'Use at least 12 characters')
		self.assertNotContains(response, 'Use at least 16 characters')

	def test_domain_profile_rejects_names_over_36_characters(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		payload = {
			'compartment_1_label': 'A' * 37,
			'board_corporation_label': 'B' * 37,
		}
		response = self.client.post(reverse('domain:edit'), payload)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Ensure this value has at most 36 characters')

	def test_domain_index_truncates_long_labels_for_display(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		DomainProfile.objects.create(
			user=self.user,
			compartment_1_label='Compartment Alpha Long',
			board_corporation_label='Personal Corporation Studio Suite',
		)
		response = self.client.get(reverse('domain:index'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Compartment')
		self.assertContains(response, 'Personal Corpor')

	def test_domain_cell_detail_loads(self):
		self.client.login(username='domainuser@example.com', password='testpass123')
		response = self.client.get(reverse('domain:cell_detail', kwargs={'slug': 'persuasive'}))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Visibility: Personal')
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
