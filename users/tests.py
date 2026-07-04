from django.test import TestCase
from django.core.management import call_command
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.urls import reverse
from django.test.utils import override_settings
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone
import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import patch

from users.models import BillingCheckoutIntent, BillingWebhookEvent, User
from users.admin import UserAdmin, PolishAdminStatusFilter


class ExecutiveSlidesAccessCommandTests(TestCase):
	def setUp(self):
		self.staff_user = User.objects.create_user(
			email="staffcmd@example.com",
			username="staffcmd",
			name="Staff Cmd",
			password="testpass123",
			is_staff=True,
		)
		self.member_user = User.objects.create_user(
			email="membercmd@example.com",
			username="membercmd",
			name="Member Cmd",
			password="testpass123",
		)

	def test_grant_by_email(self):
		call_command("manage_executive_slides_access", "--grant", "--emails", self.member_user.email)
		group = Group.objects.get(name="executive_slides_access")
		self.assertTrue(self.member_user.groups.filter(id=group.id).exists())

	def test_revoke_by_email(self):
		group, _ = Group.objects.get_or_create(name="executive_slides_access")
		self.member_user.groups.add(group)

		call_command("manage_executive_slides_access", "--revoke", "--emails", self.member_user.email)
		self.assertFalse(self.member_user.groups.filter(id=group.id).exists())

	def test_grant_all_staff(self):
		call_command("manage_executive_slides_access", "--grant", "--all-staff")
		group = Group.objects.get(name="executive_slides_access")
		self.assertTrue(self.staff_user.groups.filter(id=group.id).exists())
		self.assertFalse(self.member_user.groups.filter(id=group.id).exists())


class UserAdminPolishAccessActionTests(TestCase):
	def setUp(self):
		self.admin_user = User.objects.create_user(
			email="useradmin@example.com",
			username="useradmin",
			name="User Admin",
			password="testpass123",
			is_staff=True,
			is_superuser=True,
		)
		self.member_user = User.objects.create_user(
			email="memberpolish@example.com",
			username="memberpolish",
			name="Member Polish",
			password="testpass123",
		)
		self.site = AdminSite()
		self.admin_obj = UserAdmin(User, self.site)
		self.request_factory = RequestFactory()

	def _make_request(self):
		request = self.request_factory.post("/admin/users/user/")
		request.user = self.admin_user
		request.session = self.client.session
		setattr(request, "_messages", FallbackStorage(request))
		return request

	def test_grant_polish_admin_access_action_assigns_group(self):
		request = self._make_request()
		queryset = User.objects.filter(pk=self.member_user.pk)

		self.admin_obj.grant_polish_admin_access(request, queryset)

		self.member_user.refresh_from_db()
		self.assertTrue(self.member_user.groups.filter(name="polish_admin").exists())
		self.assertFalse(self.member_user.is_staff)

	def test_revoke_polish_admin_access_action_removes_group(self):
		group, _ = Group.objects.get_or_create(name="polish_admin")
		self.member_user.groups.add(group)
		request = self._make_request()
		queryset = User.objects.filter(pk=self.member_user.pk)

		self.admin_obj.revoke_polish_admin_access(request, queryset)

		self.member_user.refresh_from_db()
		self.assertFalse(self.member_user.groups.filter(name="polish_admin").exists())

	def test_is_polish_admin_member_indicator_reflects_group_membership(self):
		group, _ = Group.objects.get_or_create(name="polish_admin")
		self.assertFalse(self.admin_obj.is_polish_admin_member(self.member_user))
		self.member_user.groups.add(group)
		self.assertTrue(self.admin_obj.is_polish_admin_member(self.member_user))

	def test_polish_admin_filter_yes_and_no(self):
		group, _ = Group.objects.get_or_create(name="polish_admin")
		self.member_user.groups.add(group)
		non_polish_user = User.objects.create_user(
			email="plainmember@example.com",
			username="plainmember",
			name="Plain Member",
			password="testpass123",
		)

		request_yes = self.request_factory.get("/admin/users/user/", {"polish_admin": "yes"})
		params_yes = request_yes.GET.copy()
		filter_yes = PolishAdminStatusFilter(
			request_yes,
			params_yes,
			User,
			self.admin_obj,
		)
		filtered_yes = filter_yes.queryset(request_yes, User.objects.all())
		self.assertIn(self.member_user, filtered_yes)
		self.assertNotIn(non_polish_user, filtered_yes)

		request_no = self.request_factory.get("/admin/users/user/", {"polish_admin": "no"})
		params_no = request_no.GET.copy()
		filter_no = PolishAdminStatusFilter(
			request_no,
			params_no,
			User,
			self.admin_obj,
		)
		filtered_no = filter_no.queryset(request_no, User.objects.all())
		self.assertIn(non_polish_user, filtered_no)
		self.assertNotIn(self.member_user, filtered_no)


class SubscriptionUpgradeViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="subuser@example.com",
			username="subuser",
			name="Sub User",
			password="testpass123",
		)

	def test_upgrade_view_requires_login(self):
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 302)

	def test_upgrade_post_updates_subscription_tier_for_free(self):
		self.user.subscription_tier = User.SUBSCRIPTION_PREMIUM_PRO
		self.user.save(update_fields=["subscription_tier"])
		self.client.force_login(self.user)
		response = self.client.post(
			reverse("users:subscription-upgrade"),
			{"subscription_tier": User.SUBSCRIPTION_FREE},
		)
		self.assertEqual(response.status_code, 302)
		self.user.refresh_from_db()
		self.assertEqual(self.user.subscription_tier, User.SUBSCRIPTION_FREE)

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_upgrade_post_redirects_to_checkout_for_premium_tier(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_upgrade_1"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/upgrade"

		response = self.client.post(
			reverse("users:subscription-upgrade"),
			{"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], "https://checkout.stripe.test/session/upgrade")

		self.user.refresh_from_db()
		self.assertEqual(self.user.subscription_tier, User.SUBSCRIPTION_FREE)

	def test_subscription_upgrade_page_renders_timeline_block(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing Timeline")

	def test_support_context_summary_absent_when_no_billing_events(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Support context summary")

	def test_timeline_shows_pending_intent(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_pending_1",
			status=BillingCheckoutIntent.STATUS_SESSION_CREATED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Stripe session created")
		self.assertContains(response, "Pending")
		self.assertContains(response, "Stripe")

	def test_timeline_shows_generic_provider_badge_for_generic_events(self):
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="generic",
			provider_event_id="evt_generic_badge_1",
			idempotency_key="idem_generic_badge_1",
			event_type="subscription.updated",
			status=BillingWebhookEvent.STATUS_RECEIVED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Webhook received")
		self.assertContains(response, "Generic")

	def test_timeline_shows_completed_intent(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_completed_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Subscription activated")
		self.assertContains(response, "Completed")

	def test_timeline_shows_failed_intent_with_safe_error_message(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_failed_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="No Stripe price mapping configured for requested tier.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Subscription failed")
		self.assertContains(response, "Retry required")
		self.assertContains(response, "selected plan could not be mapped")

	def test_timeline_orders_webhook_outcomes_by_latest_timestamp(self):
		older_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_old",
			idempotency_key="timeline_order_old",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			error_message="Invalid webhook signature.",
		)
		newer_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_new",
			idempotency_key="timeline_order_new",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)

		now = timezone.now()
		BillingWebhookEvent.objects.filter(pk=older_event.pk).update(
			created_at=now - timedelta(hours=3),
			processed_at=now - timedelta(hours=3),
		)
		BillingWebhookEvent.objects.filter(pk=newer_event.pk).update(
			created_at=now - timedelta(minutes=5),
			processed_at=now - timedelta(minutes=5),
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		timeline = response.context["billing_timeline"]
		self.assertGreaterEqual(len(timeline), 2)
		self.assertEqual(timeline[0]["title"], "Subscription activated")
		self.assertEqual(timeline[1]["title"], "Subscription failed")

	def test_timeline_pending_filter_shows_only_pending_rows(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_filter_pending",
			status=BillingCheckoutIntent.STATUS_SESSION_CREATED,
		)
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_filter_completed",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)

		self.client.force_login(self.user)
		response = self.client.get(f"{reverse('users:subscription-upgrade')}?billing_status=pending")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Stripe session created")
		self.assertNotContains(response, "Plan activated")

	def test_timeline_completed_filter_shows_only_completed_rows(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_filter_completed_2",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_filter_failed_2",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)

		self.client.force_login(self.user)
		response = self.client.get(f"{reverse('users:subscription-upgrade')}?billing_status=completed")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Plan activated")
		self.assertNotContains(response, "Retry required")

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_upgrade_post_shows_safe_adapter_error_message(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = False
		mock_create_checkout_session.return_value.session_id = ""
		mock_create_checkout_session.return_value.checkout_url = ""
		mock_create_checkout_session.return_value.error_message = "Stripe secret key is not configured."

		response = self.client.post(
			reverse("users:subscription-upgrade"),
			{"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO},
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "temporarily unavailable")

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_checkout_session_api_returns_safe_idempotency_conflict_message(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_safe_1"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/safe"

		self.client.post(
			reverse("users:billing-checkout-session"),
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_STARTER,
				"idempotency_key": "safe_idem_1",
			},
		)
		conflict_response = self.client.post(
			reverse("users:billing-checkout-session"),
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO,
				"idempotency_key": "safe_idem_1",
			},
		)
		self.assertEqual(conflict_response.status_code, 409)
		self.assertIn("already in progress", conflict_response.json()["error"])

	def test_timeline_failed_row_renders_retry_checkout_button(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_retry_button_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Retry Checkout")

	def test_timeline_failed_row_without_reusable_tier_shows_retry_unavailable(self):
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_no_tier",
			idempotency_key="timeline_retry_unavailable_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier="",
			error_message="Invalid subscription tier in payload.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Retry unavailable")
		self.assertContains(response, "No reusable plan was found")

	def test_timeline_failed_webhook_row_renders_copy_support_context_with_event_and_idempotency(self):
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_support_1",
			idempotency_key="idem_support_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Copy support context")
		self.assertContains(response, "Support context:")
		self.assertContains(response, "event_id=evt_support_1")
		self.assertContains(response, "idempotency_key=idem_support_1")

	def test_support_context_summary_renders_latest_event_and_copy_payload(self):
		older_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_summary_old",
			idempotency_key="idem_summary_old",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_STARTER,
		)
		newer_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_summary_new",
			idempotency_key="idem_summary_new",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)
		now = timezone.now()
		BillingWebhookEvent.objects.filter(pk=older_event.pk).update(
			created_at=now - timedelta(hours=2),
			processed_at=now - timedelta(hours=2),
		)
		BillingWebhookEvent.objects.filter(pk=newer_event.pk).update(
			created_at=now - timedelta(minutes=2),
			processed_at=now - timedelta(minutes=2),
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Support context summary")
		self.assertContains(response, "Copy summary")
		self.assertContains(response, "Last event ID: evt_summary_new")
		self.assertContains(response, "Last idempotency key: idem_summary_new")
		self.assertContains(response, "Last tier: premium_pro")
		self.assertContains(response, "data-support-summary=\"source=webhook")

	def test_support_context_summary_shows_safe_failure_reason(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_summary_failed_1",
			idempotency_key="idem_summary_failed_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Support context summary")
		self.assertContains(response, "Last session ID: cs_summary_failed_1")
		self.assertContains(response, "Last failure: Billing provider setup is temporarily unavailable. Please try again later.")

	def test_support_context_diff_visible_when_latest_intent_and_webhook_mismatch(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_diff_1",
			idempotency_key="idem_diff_intent_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_diff_1",
			idempotency_key="idem_diff_webhook_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_STARTER,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Support context diff")
		self.assertContains(response, "Copy diff")
		self.assertContains(response, "Idempotency key")
		self.assertContains(response, "data-support-diff=\"intent_tier=premium_pro")

	def test_support_context_diff_absent_when_latest_intent_and_webhook_align(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="not_reported",
			idempotency_key="idem_align_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_align_1",
			idempotency_key="idem_align_1",
			event_type="not_reported",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Support context diff")
		self.assertNotContains(response, "data-support-diff=")

	def test_support_context_diff_uses_latest_records_for_ordering(self):
		older_intent = BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_old_mismatch",
			idempotency_key="idem_old_mismatch",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		older_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_old_mismatch",
			idempotency_key="idem_old_webhook",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_STARTER,
			error_message="Invalid webhook signature.",
		)

		newer_intent = BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="not_reported",
			idempotency_key="idem_new_aligned",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		newer_event = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_new_aligned",
			idempotency_key="idem_new_aligned",
			event_type="not_reported",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)

		now = timezone.now()
		BillingCheckoutIntent.objects.filter(pk=older_intent.pk).update(updated_at=now - timedelta(hours=2))
		BillingWebhookEvent.objects.filter(pk=older_event.pk).update(
			created_at=now - timedelta(hours=2),
			processed_at=now - timedelta(hours=2),
		)
		BillingCheckoutIntent.objects.filter(pk=newer_intent.pk).update(updated_at=now - timedelta(minutes=2))
		BillingWebhookEvent.objects.filter(pk=newer_event.pk).update(
			created_at=now - timedelta(minutes=2),
			processed_at=now - timedelta(minutes=2),
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Support context diff")

	def test_support_context_diff_copy_payload_contains_safe_failure_text(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_diff_safe_1",
			idempotency_key="idem_diff_safe_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_diff_safe_1",
			idempotency_key="idem_diff_safe_2",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_STARTER,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "data-support-diff=\"intent_tier=premium_pro")
		self.assertContains(
			response,
			"intent_failure_reason=Billing provider setup is temporarily unavailable. Please try again later.",
		)
		self.assertContains(
			response,
			"webhook_failure_reason=We could not verify the billing provider update. Please try again.",
		)
		self.assertNotContains(response, "Invalid webhook signature.")

	def test_billing_health_indicator_shows_healthy_state(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="not_reported",
			idempotency_key="idem_health_ok_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_health_ok_1",
			idempotency_key="idem_health_ok_1",
			event_type="not_reported",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing health")
		self.assertContains(response, "Billing healthy")

	def test_billing_health_indicator_shows_degraded_state(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_health_degraded_1",
			idempotency_key="idem_health_degraded_1",
			status=BillingCheckoutIntent.STATUS_SESSION_CREATED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing health")
		self.assertContains(response, "Billing degraded")

	def test_billing_health_indicator_shows_failing_state(self):
		for idx in range(4):
			BillingCheckoutIntent.objects.create(
				user=self.user,
				provider="stripe",
				requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
				provider_session_id=f"cs_health_fail_{idx}",
				idempotency_key=f"idem_health_fail_{idx}",
				status=BillingCheckoutIntent.STATUS_FAILED,
				error_message="Stripe secret key is not configured.",
			)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing health")
		self.assertContains(response, "Billing failing")

	def test_billing_health_indicator_uses_latest_event_window_ordering(self):
		now = timezone.now()
		for idx in range(10):
			intent = BillingCheckoutIntent.objects.create(
				user=self.user,
				provider="stripe",
				requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
				provider_session_id=f"cs_health_window_old_{idx}",
				idempotency_key=f"idem_health_window_old_{idx}",
				status=BillingCheckoutIntent.STATUS_FAILED,
				error_message="Stripe secret key is not configured.",
			)
			BillingCheckoutIntent.objects.filter(pk=intent.pk).update(updated_at=now - timedelta(days=2, minutes=idx))

		for idx in range(8):
			intent = BillingCheckoutIntent.objects.create(
				user=self.user,
				provider="stripe",
				requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
				provider_session_id="not_reported",
				idempotency_key=f"idem_health_window_new_{idx}",
				status=BillingCheckoutIntent.STATUS_COMPLETED,
			)
			BillingCheckoutIntent.objects.filter(pk=intent.pk).update(updated_at=now - timedelta(minutes=idx))
			BillingWebhookEvent.objects.create(
				user=self.user,
				provider="stripe",
				provider_event_id=f"evt_health_window_new_{idx}",
				idempotency_key=f"idem_health_window_new_{idx}",
				event_type="not_reported",
				status=BillingWebhookEvent.STATUS_PROCESSED,
				target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			)

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing healthy")

	def test_billing_health_indicator_shows_safe_text_only(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_health_safe_1",
			idempotency_key="idem_health_safe_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Billing health")
		self.assertContains(response, "Billing provider setup is temporarily unavailable. Please try again later.")
		self.assertNotContains(response, "Stripe secret key is not configured.")

	def test_billing_event_export_visible_when_events_exist(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_export_visible_1",
			idempotency_key="idem_export_visible_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Export billing events")
		self.assertContains(response, "data-billing-export=\"billing_support_bundle_v1")

	def test_billing_event_export_absent_when_no_events_exist(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "data-billing-export=")

	def test_billing_event_export_payload_contains_health_summary_diff_and_timeline(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_export_payload_1",
			idempotency_key="idem_export_payload_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_export_payload_1",
			idempotency_key="idem_export_payload_2",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_STARTER,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "billing_support_bundle_v1")
		self.assertContains(response, "[health]")
		self.assertContains(response, "[summary]")
		self.assertContains(response, "[diff]")
		self.assertContains(response, "[timeline]")
		self.assertContains(response, "timeline_1_idempotency_key=")
		self.assertContains(response, "timeline_1_provider_session_id=")

	def test_billing_event_export_payload_uses_safe_error_text_only(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_export_safe_1",
			idempotency_key="idem_export_safe_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "safe_recent_failure_reason=Billing provider setup is temporarily unavailable. Please try again later.")
		self.assertContains(response, "timeline_1_safe_error=Billing provider setup is temporarily unavailable. Please try again later.")
		self.assertNotContains(response, "Stripe secret key is not configured.")

	def test_billing_event_export_payload_uses_latest_ordering(self):
		older_intent = BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_export_old_1",
			idempotency_key="idem_export_old_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		newer_intent = BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_export_new_1",
			idempotency_key="idem_export_new_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		now = timezone.now()
		BillingCheckoutIntent.objects.filter(pk=older_intent.pk).update(updated_at=now - timedelta(hours=2))
		BillingCheckoutIntent.objects.filter(pk=newer_intent.pk).update(updated_at=now - timedelta(minutes=2))

		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "timeline_1_idempotency_key=idem_export_new_1")

	def test_webhook_reliability_sparkline_visible_with_webhook_events(self):
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_sparkline_success_1",
			idempotency_key="idem_sparkline_success_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_sparkline_failed_1",
			idempotency_key="idem_sparkline_failed_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Webhook trend")
		self.assertContains(response, "data-webhook-sparkline-point=\"success\"")
		self.assertContains(response, "data-webhook-sparkline-point=\"failed\"")

	def test_webhook_reliability_sparkline_absent_without_webhook_events(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_sparkline_no_webhook_1",
			idempotency_key="idem_sparkline_no_webhook_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Webhook trend")
		self.assertNotContains(response, "data-webhook-sparkline-point=")

	def test_webhook_reliability_sparkline_uses_chronological_order(self):
		older = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_sparkline_old",
			idempotency_key="idem_sparkline_old",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			error_message="Invalid webhook signature.",
		)
		newer = BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_sparkline_new",
			idempotency_key="idem_sparkline_new",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_PROCESSED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
		)
		now = timezone.now()
		BillingWebhookEvent.objects.filter(pk=older.pk).update(
			created_at=now - timedelta(hours=2),
			processed_at=now - timedelta(hours=2),
		)
		BillingWebhookEvent.objects.filter(pk=newer.pk).update(
			created_at=now - timedelta(minutes=2),
			processed_at=now - timedelta(minutes=2),
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		content = response.content.decode("utf-8")
		old_index = content.find('data-webhook-sparkline-id="evt_sparkline_old"')
		new_index = content.find('data-webhook-sparkline-id="evt_sparkline_new"')
		self.assertGreater(old_index, -1)
		self.assertGreater(new_index, -1)
		self.assertLess(old_index, new_index)

	def test_billing_event_inspector_modal_visible_with_timeline_rows(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_inspector_modal_1",
			idempotency_key="idem_inspector_modal_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Inspect event")
		self.assertContains(response, "billing-event-inspector-modal")

	def test_billing_event_inspector_absent_without_timeline_rows(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "data-inspect-title=")

	def test_billing_event_inspector_data_attributes_use_safe_error_text(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_inspector_safe_1",
			idempotency_key="idem_inspector_safe_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(
			response,
			"data-inspect-error=\"Billing provider setup is temporarily unavailable. Please try again later.\"",
		)
		self.assertNotContains(response, "data-inspect-error=\"Stripe secret key is not configured.\"")

	def test_failed_row_shows_full_context_toggle(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_full_toggle_1",
			idempotency_key="idem_full_toggle_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Show full context")

	def test_failed_row_full_context_renders_complete_payload(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_full_payload_1",
			idempotency_key="idem_full_payload_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "provider_session_id=cs_full_payload_1")
		self.assertContains(response, "requested_tier=premium_pro")
		self.assertContains(response, "timestamp=")

	def test_failed_row_shows_copy_full_context_button(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_full_copy_btn_1",
			idempotency_key="idem_full_copy_btn_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Copy full context")
		self.assertContains(response, "data-full-context=\"source=intent;provider=stripe")

	def test_failed_row_full_context_copy_payload_includes_expected_fields(self):
		BillingWebhookEvent.objects.create(
			user=self.user,
			provider="stripe",
			provider_event_id="evt_full_copy_1",
			idempotency_key="idem_full_copy_1",
			event_type="customer.subscription.updated",
			status=BillingWebhookEvent.STATUS_FAILED,
			target_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			error_message="Invalid webhook signature.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "data-full-context=\"source=webhook;provider=stripe")
		self.assertContains(response, "event_id=evt_full_copy_1")
		self.assertContains(response, "idempotency_key=idem_full_copy_1")
		self.assertContains(response, "event_type=customer.subscription.updated")
		self.assertContains(response, "target_tier=premium_pro")
		self.assertContains(response, "timestamp=")
		self.assertNotContains(response, "payload=")

	def test_failed_row_copy_full_context_button_is_inside_details_block(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			provider_session_id="cs_full_copy_details_1",
			idempotency_key="idem_full_copy_details_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		content = response.content.decode("utf-8")
		summary_index = content.find("Show full context")
		button_index = content.find("Copy full context")
		details_close_index = content.find("</details>", summary_index)
		self.assertGreater(summary_index, -1)
		self.assertGreater(button_index, summary_index)
		self.assertGreater(details_close_index, button_index)

	def test_successful_rows_do_not_show_full_context_toggle_and_no_raw_payload_dump(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="idem_success_no_toggle_1",
			status=BillingCheckoutIntent.STATUS_COMPLETED,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse("users:subscription-upgrade"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Show full context")
		self.assertNotContains(response, "data-full-context=")
		self.assertNotContains(response, "payload=")

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_retry_checkout_post_from_failed_timeline_redirects_to_checkout(self, mock_create_checkout_session):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="timeline_retry_post_1",
			status=BillingCheckoutIntent.STATUS_FAILED,
			error_message="Stripe secret key is not configured.",
		)
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_retry_1"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/retry"

		response = self.client.post(
			reverse("users:subscription-upgrade"),
			{"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], "https://checkout.stripe.test/session/retry")


class BillingWebhookTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="billinguser@example.com",
			username="billinguser",
			name="Billing User",
			password="testpass123",
		)
		self.url = reverse("users:billing-webhook")

	def _signature(self, secret, payload):
		raw = json.dumps(payload).encode("utf-8")
		header = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
		return raw, header

	def _stripe_signature(self, secret, payload, timestamp=1700000000):
		raw = json.dumps(payload).encode("utf-8")
		signed_payload = f"{timestamp}.{raw.decode('utf-8')}".encode("utf-8")
		v1 = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
		return raw, f"t={timestamp},v1={v1}"

	@override_settings(BILLING_WEBHOOK_SECRET="webhook-secret")
	def test_webhook_updates_subscription_tier_and_records_event(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="generic",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="idem_1",
			status=BillingCheckoutIntent.STATUS_SESSION_CREATED,
		)

		payload = {
			"event_id": "evt_1",
			"idempotency_key": "idem_1",
			"event_type": "subscription.updated",
			"data": {
				"email": self.user.email,
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO,
			},
		}
		raw, signature = self._signature("webhook-secret", payload)

		response = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_SIGNATURE=signature,
			HTTP_X_BILLING_PROVIDER="generic",
		)
		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertEqual(self.user.subscription_tier, User.SUBSCRIPTION_PREMIUM_PRO)

		event = BillingWebhookEvent.objects.get(provider="generic", idempotency_key="idem_1")
		self.assertEqual(event.status, BillingWebhookEvent.STATUS_PROCESSED)
		self.assertTrue(event.signature_valid)
		self.assertEqual(event.user, self.user)

		intent = BillingCheckoutIntent.objects.get(provider="generic", idempotency_key="idem_1")
		self.assertEqual(intent.status, BillingCheckoutIntent.STATUS_COMPLETED)

	@override_settings(BILLING_WEBHOOK_SECRET="webhook-secret")
	def test_webhook_replay_is_idempotent(self):
		payload = {
			"event_id": "evt_2",
			"idempotency_key": "idem_2",
			"event_type": "subscription.updated",
			"data": {
				"email": self.user.email,
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_STARTER,
			},
		}
		raw, signature = self._signature("webhook-secret", payload)

		response_one = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_SIGNATURE=signature,
			HTTP_X_BILLING_PROVIDER="generic",
		)
		response_two = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_SIGNATURE=signature,
			HTTP_X_BILLING_PROVIDER="generic",
		)

		self.assertEqual(response_one.status_code, 200)
		self.assertEqual(response_two.status_code, 200)
		self.assertEqual(BillingWebhookEvent.objects.filter(provider="generic", idempotency_key="idem_2").count(), 1)

	@override_settings(BILLING_WEBHOOK_SECRET="webhook-secret")
	def test_webhook_invalid_signature_fails_and_records_error(self):
		payload = {
			"event_id": "evt_3",
			"idempotency_key": "idem_3",
			"event_type": "subscription.updated",
			"data": {
				"email": self.user.email,
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_ENTERPRISE,
			},
		}
		raw = json.dumps(payload).encode("utf-8")

		response = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_SIGNATURE="bad-signature",
			HTTP_X_BILLING_PROVIDER="generic",
		)
		self.assertEqual(response.status_code, 400)
		event = BillingWebhookEvent.objects.get(provider="generic", idempotency_key="idem_3")
		self.assertEqual(event.status, BillingWebhookEvent.STATUS_FAILED)
		self.assertFalse(event.signature_valid)
		self.assertIn("Invalid webhook signature", event.error_message)

	@override_settings(
		BILLING_WEBHOOK_SECRET_STRIPE="stripe-secret",
		BILLING_STRIPE_SIGNATURE_TOLERANCE_SECONDS=2000000000,
		BILLING_STRIPE_PRICE_TIER_MAP={"price_pro": User.SUBSCRIPTION_PREMIUM_PRO},
	)
	def test_stripe_webhook_subscription_updated_uses_price_mapping(self):
		BillingCheckoutIntent.objects.create(
			user=self.user,
			provider="stripe",
			requested_tier=User.SUBSCRIPTION_PREMIUM_PRO,
			idempotency_key="stripe_idem_1",
			status=BillingCheckoutIntent.STATUS_SESSION_CREATED,
		)

		payload = {
			"id": "evt_stripe_1",
			"request": {"idempotency_key": "stripe_idem_1"},
			"type": "customer.subscription.updated",
			"data": {
				"object": {
					"customer_email": self.user.email,
					"items": {"data": [{"price": {"id": "price_pro"}}]},
				}
			},
		}
		raw, stripe_signature = self._stripe_signature("stripe-secret", payload)

		response = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_PROVIDER="stripe",
			HTTP_STRIPE_SIGNATURE=stripe_signature,
		)
		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertEqual(self.user.subscription_tier, User.SUBSCRIPTION_PREMIUM_PRO)

		event = BillingWebhookEvent.objects.get(provider="stripe", idempotency_key="stripe_idem_1")
		self.assertEqual(event.status, BillingWebhookEvent.STATUS_PROCESSED)
		self.assertTrue(event.signature_valid)

		intent = BillingCheckoutIntent.objects.get(provider="stripe", idempotency_key="stripe_idem_1")
		self.assertEqual(intent.status, BillingCheckoutIntent.STATUS_COMPLETED)

	@override_settings(
		BILLING_WEBHOOK_SECRET_STRIPE="stripe-secret",
		BILLING_STRIPE_SIGNATURE_TOLERANCE_SECONDS=2000000000,
		BILLING_STRIPE_PRICE_TIER_MAP={"price_starter": User.SUBSCRIPTION_PREMIUM_STARTER},
	)
	def test_stripe_webhook_unknown_price_fails_with_invalid_tier(self):
		payload = {
			"id": "evt_stripe_2",
			"request": {"idempotency_key": "stripe_idem_2"},
			"type": "customer.subscription.updated",
			"data": {
				"object": {
					"customer_email": self.user.email,
					"items": {"data": [{"price": {"id": "price_unknown"}}]},
				}
			},
		}
		raw, stripe_signature = self._stripe_signature("stripe-secret", payload)

		response = self.client.post(
			self.url,
			data=raw,
			content_type="application/json",
			HTTP_X_BILLING_PROVIDER="stripe",
			HTTP_STRIPE_SIGNATURE=stripe_signature,
		)
		self.assertEqual(response.status_code, 400)
		event = BillingWebhookEvent.objects.get(provider="stripe", idempotency_key="stripe_idem_2")
		self.assertEqual(event.status, BillingWebhookEvent.STATUS_FAILED)
		self.assertIn("Invalid subscription tier", event.error_message)


class BillingCheckoutSessionTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="checkoutuser@example.com",
			username="checkoutuser",
			name="Checkout User",
			password="testpass123",
		)
		self.url = reverse("users:billing-checkout-session")

	def test_checkout_session_requires_login(self):
		response = self.client.post(
			self.url,
			{"provider": "stripe", "subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO},
		)
		self.assertEqual(response.status_code, 302)

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_checkout_session_creates_intent(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_test_1"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/1"
		mock_create_checkout_session.return_value.error_message = ""

		response = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO,
				"idempotency_key": "checkout_idem_1",
			},
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload["ok"])

		intent = BillingCheckoutIntent.objects.get(
			user=self.user,
			provider="stripe",
			idempotency_key="checkout_idem_1",
		)
		self.assertEqual(intent.status, BillingCheckoutIntent.STATUS_SESSION_CREATED)
		self.assertEqual(intent.provider_session_id, "cs_test_1")
		self.assertEqual(intent.checkout_url, "https://checkout.stripe.test/session/1")

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_checkout_session_idempotent_replay_returns_existing_intent(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_test_2"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/2"

		response_one = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_STARTER,
				"idempotency_key": "checkout_idem_2",
			},
		)
		response_two = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_STARTER,
				"idempotency_key": "checkout_idem_2",
			},
		)

		self.assertEqual(response_one.status_code, 200)
		self.assertEqual(response_two.status_code, 200)
		self.assertEqual(
			BillingCheckoutIntent.objects.filter(user=self.user, provider="stripe", idempotency_key="checkout_idem_2").count(),
			1,
		)
		self.assertEqual(mock_create_checkout_session.call_count, 1)
		self.assertTrue(response_two.json().get("duplicate"))

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_checkout_session_idempotency_conflict_returns_409(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = True
		mock_create_checkout_session.return_value.session_id = "cs_test_3"
		mock_create_checkout_session.return_value.checkout_url = "https://checkout.stripe.test/session/3"

		first = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_STARTER,
				"idempotency_key": "checkout_idem_3",
			},
		)
		second = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_PRO,
				"idempotency_key": "checkout_idem_3",
			},
		)

		self.assertEqual(first.status_code, 200)
		self.assertEqual(second.status_code, 409)

	@patch("users.billing.StripeBillingProviderAdapter.create_checkout_session")
	def test_checkout_session_adapter_failure_records_failed_intent(self, mock_create_checkout_session):
		self.client.force_login(self.user)
		mock_create_checkout_session.return_value.success = False
		mock_create_checkout_session.return_value.session_id = ""
		mock_create_checkout_session.return_value.checkout_url = ""
		mock_create_checkout_session.return_value.error_message = "stripe api unavailable"

		response = self.client.post(
			self.url,
			{
				"provider": "stripe",
				"subscription_tier": User.SUBSCRIPTION_PREMIUM_ENTERPRISE,
				"idempotency_key": "checkout_idem_4",
			},
		)
		self.assertEqual(response.status_code, 502)

		intent = BillingCheckoutIntent.objects.get(
			user=self.user,
			provider="stripe",
			idempotency_key="checkout_idem_4",
		)
		self.assertEqual(intent.status, BillingCheckoutIntent.STATUS_FAILED)
		self.assertIn("stripe api unavailable", intent.error_message)
