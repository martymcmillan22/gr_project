from django.test import TestCase
from django.urls import reverse

from users.models import User
from .models import ExpoFact, POVResponse


def make_user(email, username):
    return User.objects.create_user(
        email=email, username=username, name=username, password='testpass123'
    )


def make_fact(user, title='Test Fact Set', active=True):
    return ExpoFact.objects.create(
        title=title,
        content='Here are the facts about X.',
        created_by=user,
        is_active=active,
    )


class PovsHomeTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff@example.com', 'staff')
        self.user = make_user('viewer@example.com', 'viewer')

    def test_home_requires_login(self):
        response = self.client.get(reverse('povs-home'))
        self.assertEqual(response.status_code, 302)

    def test_home_lists_active_facts_only(self):
        make_fact(self.staff, 'Active Fact')
        make_fact(self.staff, 'Inactive Fact', active=False)

        self.client.login(username='viewer@example.com', password='testpass123')
        response = self.client.get(reverse('povs-home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Fact')
        self.assertNotContains(response, 'Inactive Fact')

    def test_home_shows_progress_for_started_response(self):
        fact = make_fact(self.staff)
        POVResponse.objects.create(user=self.user, expo_fact=fact, first_person='My view')

        self.client.login(username='viewer@example.com', password='testpass123')
        response = self.client.get(reverse('povs-home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue')


class POVGateTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff2@example.com', 'staff2')
        self.user = make_user('gateuser@example.com', 'gateuser')
        self.fact = make_fact(self.staff)
        self.url = reverse('povs-detail', kwargs={'pk': self.fact.pk})
        self.client.login(username='gateuser@example.com', password='testpass123')

    def test_detail_page_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_detail_page_shows_red_facts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Fact Set')
        self.assertContains(response, 'Here are the facts about X.')

    def test_prediction_gate_blocks_without_first_person(self):
        response = self.client.post(self.url, {'stage': 'prediction', 'prediction': 'I predict X.'})
        self.assertEqual(response.status_code, 302)

        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertFalse(pov.prediction.strip())

    def test_narrative_gate_blocks_without_prediction(self):
        POVResponse.objects.create(user=self.user, expo_fact=self.fact, first_person='My view')
        response = self.client.post(self.url, {'stage': 'narrative', 'narrative': 'Advise X.'})
        self.assertEqual(response.status_code, 302)

        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertFalse(pov.narrative.strip())

    def test_probable_outcome_gate_blocks_without_narrative(self):
        POVResponse.objects.create(
            user=self.user, expo_fact=self.fact,
            first_person='My view', prediction='I predict X.',
        )
        response = self.client.post(self.url, {'stage': 'probable_outcome', 'probable_outcome': 'Outcome Y.'})
        self.assertEqual(response.status_code, 302)

        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertFalse(pov.probable_outcome.strip())

    def test_full_pov_flow_completes_all_stages_in_order(self):
        # Blue
        self.client.post(self.url, {'stage': 'first_person', 'first_person': 'I think this matters.'})
        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertEqual(pov.first_person, 'I think this matters.')
        self.assertIsNotNone(pov.first_person_at)

        # Green
        self.client.post(self.url, {'stage': 'prediction', 'prediction': 'I predict growth.'})
        pov.refresh_from_db()
        self.assertEqual(pov.prediction, 'I predict growth.')
        self.assertIsNotNone(pov.prediction_at)

        # Yellow
        self.client.post(self.url, {'stage': 'narrative', 'narrative': 'Double down on messaging.'})
        pov.refresh_from_db()
        self.assertEqual(pov.narrative, 'Double down on messaging.')
        self.assertIsNotNone(pov.narrative_at)

        # Green-Lime
        self.client.post(self.url, {'stage': 'probable_outcome', 'probable_outcome': 'Market responds well.'})
        pov.refresh_from_db()
        self.assertEqual(pov.probable_outcome, 'Market responds well.')
        self.assertIsNotNone(pov.probable_outcome_at)

    def test_blue_unlocks_green_form_in_response(self):
        POVResponse.objects.create(user=self.user, expo_fact=self.fact, first_person='My view')
        response = self.client.get(self.url)
        self.assertContains(response, 'name="stage" value="prediction"')

    def test_green_locked_without_blue_in_response(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'name="stage" value="prediction"')

    def test_yellow_unlocks_only_after_green(self):
        POVResponse.objects.create(
            user=self.user, expo_fact=self.fact,
            first_person='My view', prediction='I predict X.',
        )
        response = self.client.get(self.url)
        self.assertContains(response, 'name="stage" value="narrative"')

    def test_yellow_locked_without_green(self):
        POVResponse.objects.create(user=self.user, expo_fact=self.fact, first_person='My view')
        response = self.client.get(self.url)
        self.assertNotContains(response, 'name="stage" value="narrative"')

    def test_lime_unlocks_only_after_yellow(self):
        POVResponse.objects.create(
            user=self.user, expo_fact=self.fact,
            first_person='My view', prediction='I predict X.', narrative='Advise them.',
        )
        response = self.client.get(self.url)
        self.assertContains(response, 'name="stage" value="probable_outcome"')

    def test_each_stage_is_editable_after_submission(self):
        POVResponse.objects.create(user=self.user, expo_fact=self.fact, first_person='First draft')
        self.client.post(self.url, {'stage': 'first_person', 'first_person': 'Revised view'})
        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertEqual(pov.first_person, 'Revised view')

    def test_edit_preserves_original_timestamp(self):
        from django.utils import timezone as tz
        import datetime
        original_time = tz.now() - datetime.timedelta(days=1)
        POVResponse.objects.create(
            user=self.user, expo_fact=self.fact,
            first_person='First draft',
            first_person_at=original_time,
        )
        self.client.post(self.url, {'stage': 'first_person', 'first_person': 'Revised view'})
        pov = POVResponse.objects.get(user=self.user, expo_fact=self.fact)
        self.assertEqual(pov.first_person, 'Revised view')
        # Timestamp must not have been overwritten
        self.assertAlmostEqual(
            pov.first_person_at.timestamp(),
            original_time.timestamp(),
            delta=1,
        )


class UserCreatedPOVTests(TestCase):
    def setUp(self):
        self.user = make_user('creator@example.com', 'creator')
        self.other = make_user('other@example.com', 'other')
        self.create_url = reverse('povs-create')
        self.client.login(username='creator@example.com', password='testpass123')

    def test_create_page_requires_login(self):
        self.client.logout()
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_create_page_loads(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Own POV')

    def test_create_saves_fact_owned_by_user(self):
        response = self.client.post(self.create_url, {
            'title': 'My own topic',
            'content': 'These are facts I want to work through.',
        })
        self.assertEqual(response.status_code, 302)
        fact = ExpoFact.objects.get(title='My own topic')
        self.assertEqual(fact.created_by, self.user)
        self.assertTrue(fact.is_active)

    def test_create_redirects_to_detail_for_immediate_response(self):
        response = self.client.post(self.create_url, {
            'title': 'Topic',
            'content': 'Some context.',
        })
        fact = ExpoFact.objects.get(title='Topic')
        self.assertRedirects(response, reverse('povs-detail', kwargs={'pk': fact.pk}))

    def test_user_created_fact_appears_in_my_povs_section(self):
        make_fact(self.user, 'My Topic')
        response = self.client.get(reverse('povs-home'))
        self.assertContains(response, 'My POVs')
        self.assertContains(response, 'My Topic')

    def test_edit_page_loads_for_owner(self):
        fact = make_fact(self.user, 'Editable Topic')
        response = self.client.get(reverse('povs-edit', kwargs={'pk': fact.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editable Topic')

    def test_edit_saves_updated_fact(self):
        fact = make_fact(self.user, 'Original Title')
        self.client.post(reverse('povs-edit', kwargs={'pk': fact.pk}), {
            'title': 'Revised Title',
            'content': 'Updated content.',
        })
        fact.refresh_from_db()
        self.assertEqual(fact.title, 'Revised Title')

    def test_edit_blocked_for_non_owner(self):
        fact = make_fact(self.user, 'Protected Topic')
        self.client.logout()
        self.client.login(username='other@example.com', password='testpass123')
        response = self.client.get(reverse('povs-edit', kwargs={'pk': fact.pk}))
        self.assertEqual(response.status_code, 404)

    def test_community_facts_not_in_my_povs(self):
        make_fact(self.other, 'Their Topic')
        response = self.client.get(reverse('povs-home'))
        self.assertContains(response, 'Community POVs')
        self.assertContains(response, 'Their Topic')
