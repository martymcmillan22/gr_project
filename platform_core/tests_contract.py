from datetime import timedelta
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from platform_core.models import (
    ClientContractProfile,
    ContractBillingAccessLink,
    CustomerTenantMembership,
    ContractBillingJob,
    ContractBillingNotification,
    ContractBillingSnapshot,
    ContractUsageEvent,
    SemanticPreset,
    Slide,
)
from platform_core.unified_admin import (
    BILLING_ACCESS_DEFAULT_TTL_DAYS,
    _billing_access_token,
    _billing_health_score_change_payload,
)


class ContractIntelligenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin_user = user_model.objects.create_superuser(
            username="contract_admin",
            email="contract_admin@example.com",
            password="password12345",
        )
        cls.customer_user = user_model.objects.create_user(
            username="billing_customer",
            name="Billing Customer",
            email="billing_customer@example.com",
            password="password12345",
        )
        ClientContractProfile.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            display_name="Profiled Client",
            billing_contact_email="billing@example.com",
            billing_plan="pro",
            monthly_event_allowance=5,
            overage_rate="0.0500",
            default_schema_version="1.0.0",
            default_capabilities="legacy_only",
            strict_negotiation=False,
            strict_payload_shape=True,
            is_active=True,
        )
        ClientContractProfile.objects.create(
            tenant_key="tenant_beta",
            client_key="profiled_client",
            display_name="Profiled Client Beta",
            billing_plan="enterprise",
            monthly_event_allowance=50,
            overage_rate="0.0200",
            default_schema_version="1.1.0",
            default_capabilities="roadmap_ref",
            strict_negotiation=False,
            strict_payload_shape=False,
            is_active=True,
        )
        CustomerTenantMembership.objects.create(
            user=cls.customer_user,
            tenant_key="default",
            client_key="profiled_client",
            role="billing",
            is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_schema_endpoint_exposes_stability_and_policy(self):
        response = self.client.get("/admin/insights-retrospective-export-schema/")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertIn("schema_hash", data)
        self.assertIn("stability_window", data)
        self.assertIn("deprecation_policy", data)
        self.assertIn("evolution_roadmap", data)
        self.assertIn("compatibility_matrix", data)
        self.assertIn("version_aliases", data)
        self.assertIn("contract_lifecycle_states", data)
        self.assertIn("schema_negotiation_hint", data)
        self.assertIn("0.9.0", data["contract_lifecycle_states"])
        self.assertEqual(data["contract_lifecycle_states"]["0.9.0"]["lifecycle_state"], "sunset")

    def test_schema_diff_endpoint_returns_expected_shape(self):
        response = self.client.get(
            "/admin/insights-retrospective-export-schema-diff/?from=1.0.0&to=1.1.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["from_version"], "1.0.0")
        self.assertEqual(data["to_version"], "1.1.0")
        self.assertIn("optional_added", data)
        self.assertIn("breaking_change_detected", data)

    def test_contract_selftest_endpoint_passes(self):
        response = self.client.get("/admin/insights-retrospective-contract-selftest/")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["passed"])
        self.assertIn("checks", data)
        self.assertGreaterEqual(len(data["checks"]), 1)

    def test_retro_export_json_contains_contract_intelligence(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertIn("schema_hash", data)
        self.assertIn("schema_notes", data)
        self.assertIn("stability_window", data["schema_notes"])
        self.assertIn("deprecation_policy", data["schema_notes"])
        self.assertIn("evolution_roadmap", data["schema_notes"])
        self.assertIn("schema_negotiation", data)

    def test_retro_export_json_supports_schema_version_negotiation(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.1.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertIn("schema_roadmap_ref", data)

    def test_retro_export_json_rejects_unknown_schema_version(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=9.9.9"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()

        self.assertEqual(data["error"], "Unsupported schema_version")
        self.assertIn("available_versions", data)

    def test_retro_export_json_supports_default_schema_pinning(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&default_schema_version=1.0.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertEqual(data["default_schema_version"], "1.0.0")

    def test_retro_export_json_multi_version_bundle(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_versions=1.0.0,1.1.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["export_format"], "basetrue-retrospective-json-multi")
        self.assertIn("versions", data)
        self.assertIn("1.0.0", data["versions"])
        self.assertIn("1.1.0", data["versions"])
        self.assertEqual(data["versions"]["1.0.0"]["schema_version"], "1.0.0")
        self.assertEqual(data["versions"]["1.1.0"]["schema_version"], "1.1.0")

    def test_retro_export_json_multi_version_migration_bundle_alias(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_versions=migration_bundle"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["requested_versions"], ["1.0.0", "1.1.0"])
        self.assertIn("1.0.0", data["versions"])
        self.assertIn("1.1.0", data["versions"])

    def test_retro_export_json_supports_version_aliasing(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=lts"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")

    def test_retro_export_json_capability_negotiation_selects_best_schema(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&client=legacy_csv_bridge&capabilities=legacy_only"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertEqual(data["schema_selection_source"], "negotiated")

    def test_retro_export_json_capability_negotiation_strict_success(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&client=legacy_csv_bridge&capabilities=legacy_only&strict_negotiation=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertEqual(data["schema_selection_source"], "negotiated-strict")
        self.assertTrue(data["strict_negotiation"])

    def test_retro_export_json_capability_negotiation_strict_conflict_fails(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&capabilities=legacy_only,roadmap_ref&strict_negotiation=1"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()

        self.assertEqual(data["error"], "No compatible schema_version for strict negotiation")
        self.assertIn("available_versions", data)

    def test_retro_export_json_strict_payload_shape_v100_strips_new_fields(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.0.0&strict_payload_shape=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertNotIn("schema_roadmap_ref", data)
        self.assertNotIn("schema_negotiation", data)
        self.assertNotIn("strict_payload_shape", data)

    def test_retro_export_json_strict_payload_shape_v110_keeps_roadmap_only(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.1.0&strict_payload_shape=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertIn("schema_roadmap_ref", data)
        self.assertNotIn("schema_negotiation", data)
        self.assertNotIn("strict_payload_shape", data)

    def test_retro_export_json_multi_strict_payload_shape_applies_per_version(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&schema_versions=1.0.0,1.1.0&strict_payload_shape=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("versions", data)
        payload_v100 = data["versions"]["1.0.0"]
        payload_v110 = data["versions"]["1.1.0"]

        self.assertNotIn("schema_roadmap_ref", payload_v100)
        self.assertIn("schema_roadmap_ref", payload_v110)
        self.assertNotIn("schema_negotiation", payload_v100)
        self.assertNotIn("schema_negotiation", payload_v110)

    def test_schema_endpoint_negotiation_hint_for_legacy_client(self):
        response = self.client.get(
            "/admin/insights-retrospective-export-schema/?client=legacy_csv_bridge"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(
            data["schema_negotiation_hint"]["recommended_version"],
            "1.0.0",
        )

    def test_schema_endpoint_respects_default_schema_pin(self):
        response = self.client.get(
            "/admin/insights-retrospective-export-schema/?default_schema_version=1.0.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["default_schema_version"], "1.0.0")

    def test_export_uses_client_profile_defaults(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertNotIn("schema_roadmap_ref", data)
        self.assertNotIn("schema_negotiation", data)

    def test_export_explicit_schema_overrides_client_profile_default(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client&schema_version=1.1.0"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")

    def test_negotiation_explicit_capabilities_override_client_profile(self):
        response = self.client.get(
            "/admin/insights-retrospective-negotiate/?client=profiled_client&capabilities=roadmap_ref"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["recommendation"]["selected_version"], "1.1.0")
        self.assertIn("applied_client_profile", data["inputs"])
        self.assertEqual(data["inputs"]["applied_client_profile"]["client_key"], "profiled_client")

    def test_usage_event_recorded_for_negotiate_and_export(self):
        before_count = ContractUsageEvent.objects.count()

        response1 = self.client.get(
            "/admin/insights-retrospective-negotiate/?client=profiled_client"
        )
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client"
        )
        self.assertEqual(response2.status_code, 200)

        after_count = ContractUsageEvent.objects.count()
        self.assertGreaterEqual(after_count, before_count + 2)
        self.assertTrue(ContractUsageEvent.objects.filter(endpoint="negotiate").exists())
        self.assertTrue(ContractUsageEvent.objects.filter(endpoint="export").exists())
        self.assertTrue(ContractUsageEvent.objects.filter(billable_units__gte=1).exists())

    def test_usage_analytics_endpoint_returns_expected_shape(self):
        self.client.get("/admin/insights-retrospective-negotiate/?client=profiled_client")
        response = self.client.get("/admin/insights-contract-usage-analytics/?window_days=30")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("window_days", data)
        self.assertIn("total_events", data)
        self.assertIn("status_breakdown", data)
        self.assertIn("billable_units_total", data)
        self.assertIn("billable_amount_total", data)
        self.assertIn("top_clients", data)
        self.assertIn("endpoint_breakdown", data)

    def test_billing_summary_endpoint_returns_expected_shape(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        response = self.client.get("/admin/insights-contract-billing-summary/?window_days=30")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("window_days", data)
        self.assertIn("summary", data)
        self.assertGreaterEqual(len(data["summary"]), 1)
        row = data["summary"][0]
        self.assertIn("billable_units", row)
        self.assertIn("estimated_amount", row)
        self.assertIn("billing_plan", row)
        self.assertIn("usage_pct", row)
        self.assertIn("enforcement_state", row)
        self.assertIn("enforcement_action", row)
        self.assertIn("enforcement_mode", row)
        self.assertIn("invoice_export_csv", row)

    def test_billing_summary_endpoint_filters_by_tenant_and_client(self):
        self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&tenant=tenant_beta&client=profiled_client"
        )
        response = self.client.get(
            "/admin/insights-contract-billing-summary/?window_days=30&tenant=tenant_beta&client=profiled_client"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["tenant_key"], "tenant_beta")
        self.assertEqual(data["client_key"], "profiled_client")
        self.assertGreaterEqual(len(data["summary"]), 1)
        self.assertTrue(all(row["tenant_key"] == "tenant_beta" for row in data["summary"]))

    def test_billing_summary_csv_export_downloads(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        response = self.client.get("/admin/insights-contract-billing-summary/?window_days=30&format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("tenant_key,client_key,billing_plan", response.content.decode("utf-8"))

    def test_billing_summary_hard_enforcement_action_present_when_exceeded(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        response = self.client.get("/admin/insights-contract-billing-summary/?window_days=30&client=profiled_client")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        row = data["summary"][0]
        self.assertEqual(row["enforcement_mode"], "hard")
        self.assertTrue(row["hard_action_url"])

    def test_billing_enforcement_endpoint_executes_strict_mode(self):
        response = self.client.get(
            "/admin/insights-contract-enforcement/?tenant=default&client=profiled_client&action=enforce_strict_mode"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])

        profile = ClientContractProfile.objects.get(tenant_key="default", client_key="profiled_client")
        self.assertTrue(profile.strict_negotiation)
        self.assertTrue(profile.strict_payload_shape)

    def test_billing_summary_can_persist_snapshot_history(self):
        before_count = ContractBillingSnapshot.objects.count()
        response = self.client.get(
            "/admin/insights-contract-billing-summary/?window_days=30&client=profiled_client&persist_snapshot=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["snapshot_created"])
        self.assertIn("snapshot_history", data)
        self.assertGreater(ContractBillingSnapshot.objects.count(), before_count)

    def test_customer_billing_page_renders(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        response = self.client.get("/contracts/billing/?tenant=default&client=profiled_client")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Billing")

    def test_customer_billing_page_requires_signed_access_for_non_staff(self):
        self.client.logout()
        response = self.client.get("/contracts/billing/?tenant=default&client=profiled_client")
        self.assertEqual(response.status_code, 403)

        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 200)

    def test_logged_in_customer_membership_grants_billing_access(self):
        self.client.force_login(self.customer_user)
        response = self.client.get("/contracts/billing/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Tenant Identity")

    def test_customer_billing_page_shows_notifications(self):
        self.client.get(
            "/admin/insights-contract-billing-jobs-queue/?tenant=default&client=profiled_client&job_type=billing_cycle&window_days=30"
        )
        self.client.get("/admin/insights-contract-billing-jobs-process/?limit=10")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Billing Notifications")

    def test_customer_billing_page_shows_insights_panel(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Billing Insights")
        self.assertContains(response, "Billing Health")
        self.assertContains(response, "Billing Health Explainer")
        self.assertContains(response, "Access-Link Risk")
        self.assertContains(response, "Why Your Score Changed")
        self.assertContains(response, "Customer Billing Forecast")
        self.assertContains(response, "Customer Link-Usage Insights")

    def test_customer_invoice_center_renders(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/invoices/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invoice Download Center")

    def test_customer_invoice_center_shows_timeline(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/invoices/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Invoice Timeline")
        self.assertContains(response, "Customer Invoice Event Feed")

    def test_customer_invoice_export_contains_signature(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/invoice/?tenant=default&client=profiled_client&window_days=30&access_token={token}&format=json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["summary"]), 1)
        self.assertIn("invoice_signature", data["summary"][0])
        self.assertIn("invoice_number", data["summary"][0])
        self.assertIn("invoice_line_items", data["summary"][0])
        self.assertGreaterEqual(len(data["summary"][0]["invoice_line_items"]), 1)
        self.assertIn("total_due", data["summary"][0])

    def test_customer_invoice_export_pdf_downloads(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        token = _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            f"/contracts/billing/invoice/?tenant=default&client=profiled_client&window_days=30&access_token={token}&format=pdf"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_revoked_billing_access_link_blocks_customer_page(self):
        token = _billing_access_token("default", "profiled_client", 30)
        link = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
        ).latest("created_at")
        revoke_response = self.client.get(
            f"/admin/insights-contract-billing-access-links/?action=revoke&link_id={link.id}"
        )
        self.assertEqual(revoke_response.status_code, 200)

        self.client.logout()
        response = self.client.get(
            f"/contracts/billing/?tenant=default&client=profiled_client&window_days=30&access_token={token}"
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_billing_console_can_issue_access_link_via_post(self):
        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "issue_access_link",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "recipient_email": "billing@example.com",
                "label": "Admin issued link",
                "window_days": 30,
                "ttl_days": 7,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ContractBillingAccessLink.objects.filter(
                tenant_key="default",
                client_key="profiled_client",
                label="Admin issued link",
            ).exists()
        )

    def test_admin_billing_console_can_revoke_access_link_via_post(self):
        token = _billing_access_token("default", "profiled_client", 30)
        link = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
        ).latest("created_at")
        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "revoke_access_link",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "link_id": link.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertFalse(link.is_active)

    def test_access_link_history_controls_render_on_insights_page(self):
        response = self.client.get("/admin/basetrue-insights/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="billing_link_status"')
        self.assertContains(response, 'name="billing_link_expires"')
        self.assertContains(response, 'name="billing_link_tenant"')
        self.assertContains(response, 'name="billing_link_client"')
        self.assertContains(response, 'name="billing_link_sort"')

    def test_access_link_history_filters_apply_status_expiry_and_tenant(self):
        now = timezone.now()
        ContractBillingAccessLink.objects.create(
            tenant_key="tenant_alpha",
            client_key="alpha_active",
            window_days=30,
            label="Alpha active",
            expires_at=now + timedelta(days=2),
            use_count=1,
            is_active=True,
        )
        ContractBillingAccessLink.objects.create(
            tenant_key="tenant_alpha",
            client_key="alpha_expired",
            window_days=30,
            label="Alpha expired",
            expires_at=now - timedelta(days=1),
            use_count=9,
            is_active=True,
        )
        ContractBillingAccessLink.objects.create(
            tenant_key="tenant_beta",
            client_key="beta_revoked",
            window_days=30,
            label="Beta revoked",
            expires_at=now + timedelta(days=4),
            revoked_at=now,
            use_count=5,
            is_active=False,
        )

        response = self.client.get(
            "/admin/basetrue-insights/",
            {
                "billing_link_status": "expired",
                "billing_link_expires": "expired",
                "billing_link_tenant": "tenant_alpha",
                "billing_link_sort": "most_used",
            },
        )
        self.assertEqual(response.status_code, 200)

        history = response.context["contract_billing_dashboard"]["access_links_history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["tenant_key"], "tenant_alpha")
        self.assertEqual(history[0]["client_key"], "alpha_expired")
        self.assertEqual(history[0]["status"], "expired")

    def test_admin_billing_console_can_bulk_revoke_filtered_links(self):
        _billing_access_token("default", "profiled_client", 30)
        _billing_access_token("default", "profiled_client", 30)
        self.assertGreaterEqual(
            ContractBillingAccessLink.objects.filter(
                tenant_key="default",
                client_key="profiled_client",
                is_active=True,
            ).count(),
            1,
        )

        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "bulk_revoke_filtered_access_links",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "active",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
                "bulk_revoke_confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ContractBillingAccessLink.objects.filter(
                tenant_key="default",
                client_key="profiled_client",
                is_active=True,
            ).count(),
            0,
        )

    def test_bulk_revoke_filtered_links_requires_confirmation(self):
        _billing_access_token("default", "profiled_client", 30)
        active_before = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
            is_active=True,
        ).count()
        self.assertGreaterEqual(active_before, 1)

        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "bulk_revoke_filtered_access_links",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "active",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
            },
        )
        self.assertEqual(response.status_code, 302)
        active_after = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
            is_active=True,
        ).count()
        self.assertEqual(active_after, active_before)

    def test_access_link_audit_export_csv_returns_filtered_rows(self):
        _billing_access_token("default", "profiled_client", 30)
        response = self.client.get(
            "/admin/insights-contract-billing-access-links-audit/",
            {
                "tenant": "default",
                "client": "profiled_client",
                "window_days": 30,
                "format": "csv",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8")
        self.assertIn("tenant_key", content)
        self.assertIn("default", content)
        self.assertIn("profiled_client", content)

    def test_bulk_issue_preset_batch_creates_access_links(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        before_count = ContractBillingAccessLink.objects.count()
        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "bulk_issue_preset_batch",
                "billing_tenant": "default",
                "billing_client": "",
                "preset_batch_size": 5,
                "window_days": 30,
                "ttl_days": 7,
                "label": "Preset batch issue",
            },
        )
        self.assertEqual(response.status_code, 302)
        after_count = ContractBillingAccessLink.objects.count()
        self.assertGreater(after_count, before_count)

    def test_send_invoice_email_action_creates_invoice_email_notification(self):
        self.client.get("/admin/insights-retrospective-export/?period=monthly&format=json&client=profiled_client")
        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "send_invoice_email",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "invoice_tenant": "default",
                "invoice_client": "profiled_client",
                "recipient_email": "billing@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        notification = ContractBillingNotification.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
            channel="invoice_email",
        ).order_by("-created_at").first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, "billing@example.com")
        self.assertIn(notification.status, {"sent", "failed", "skipped"})

    def test_billing_micro_trends_render_in_insights_context(self):
        _billing_access_token("default", "profiled_client", 30)
        response = self.client.get("/admin/basetrue-insights/")
        self.assertEqual(response.status_code, 200)
        dashboard = response.context["contract_billing_dashboard"]
        trends = dashboard.get("micro_trends", {})
        self.assertEqual(trends.get("window_days"), 7)
        self.assertEqual(len(trends.get("link_activity_rows", [])), 7)
        self.assertEqual(len(trends.get("invoice_email_rows", [])), 7)
        self.assertIn("access_link_risk", dashboard)
        self.assertIn("health_explainer", dashboard)

    def test_bounce_diagnostics_include_categories(self):
        ContractBillingNotification.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            channel="invoice_email",
            recipient="billing@example.com",
            subject="Invoice",
            body="Body",
            status="failed",
            last_error="Mailbox full",
        )
        response = self.client.get(
            "/admin/basetrue-insights/",
            {
                "billing_tenant": "default",
                "billing_client": "profiled_client",
            },
        )
        self.assertEqual(response.status_code, 200)
        diagnostics = response.context["contract_billing_dashboard"]["invoice_email_diagnostics"]
        self.assertGreaterEqual(len(diagnostics.get("categories", [])), 1)
        self.assertEqual(diagnostics["categories"][0]["key"], "mailbox_full")

    def test_admin_dashboard_exposes_resolution_and_rotation_analytics(self):
        now = timezone.now()
        ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="Rotation candidate",
            is_active=False,
            revoked_at=now,
        )
        ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="Rotation candidate",
            is_active=True,
            expires_at=now + timedelta(days=7),
        )
        response = self.client.get("/admin/basetrue-insights/")
        self.assertEqual(response.status_code, 200)
        dashboard = response.context["contract_billing_dashboard"]
        self.assertIn("anomaly_resolution_history", dashboard)
        self.assertIn("link_rotation_analytics", dashboard)
        self.assertIn("access_link_anomaly_groups", dashboard)
        self.assertIn("invoice_deliverability_heatmap", dashboard)
        self.assertIn("severity_label", dashboard["access_link_risk"])
        self.assertGreaterEqual(len(dashboard["access_link_risk"].get("threshold_bands", [])), 1)
        self.assertGreaterEqual(
            dashboard["link_rotation_analytics"].get("estimated_rotations", 0),
            1,
        )

    def test_admin_dashboard_shows_deliverability_heatmap_rows(self):
        ContractBillingNotification.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            channel="invoice_email",
            recipient="billing@example.com",
            subject="Invoice",
            body="Body",
            status="sent",
        )
        response = self.client.get("/admin/basetrue-insights/")
        self.assertEqual(response.status_code, 200)
        heatmap = response.context["contract_billing_dashboard"]["invoice_deliverability_heatmap"]
        self.assertGreaterEqual(len(heatmap.get("rows", [])), 1)
        self.assertEqual(len(heatmap.get("bucket_labels", [])), 4)

    def test_health_score_change_direction_flips_with_risk_trend(self):
        worsening = _billing_health_score_change_payload(
            health_score={"score": 70},
            access_link_risk_trend={"rows": [{"score": 40}, {"score": 80}]},
            anomalies={"total": 2},
            email_diagnostics={"failed": 1, "bounce_like": 1},
        )
        self.assertEqual(worsening["direction"], "down")
        self.assertLess(worsening["delta"], 0)

        improving = _billing_health_score_change_payload(
            health_score={"score": 70},
            access_link_risk_trend={"rows": [{"score": 80}, {"score": 40}]},
            anomalies={"total": 0},
            email_diagnostics={"failed": 0, "bounce_like": 0},
        )
        self.assertEqual(improving["direction"], "up")
        self.assertGreater(improving["delta"], 0)

    def test_resolve_access_link_anomaly_can_revoke_link(self):
        link = ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="Anomaly target",
            is_active=True,
        )
        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "resolve_access_link_anomaly",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "all",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
                "link_id": link.id,
                "resolve_mode": "revoke",
            },
        )
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertFalse(link.is_active)
        self.assertIsNotNone(link.revoked_at)

    def test_resolve_access_link_anomaly_can_rotate_link(self):
        link = ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="Rotate target",
            is_active=True,
        )
        before_count = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
        ).count()

        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "resolve_access_link_anomaly",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "all",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
                "link_id": link.id,
                "resolve_mode": "rotate",
            },
        )

        self.assertEqual(response.status_code, 302)
        after_count = ContractBillingAccessLink.objects.filter(
            tenant_key="default",
            client_key="profiled_client",
        ).count()
        self.assertEqual(after_count, before_count + 1)

        replacement = ContractBillingAccessLink.objects.exclude(id=link.id).filter(
            tenant_key="default",
            client_key="profiled_client",
            label="Rotate target",
        ).order_by("-created_at").first()
        self.assertIsNotNone(replacement)
        self.assertNotEqual(replacement.id, link.id)
        self.assertTrue(replacement.is_active)
        self.assertIsNotNone(replacement.expires_at)

        now = timezone.now()
        expected = now + timedelta(days=BILLING_ACCESS_DEFAULT_TTL_DAYS)
        self.assertGreaterEqual(replacement.expires_at, expected - timedelta(minutes=2))
        self.assertLessEqual(replacement.expires_at, expected + timedelta(minutes=2))

    def test_rotate_action_revokes_original_and_records_rotation_history(self):
        link = ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="History rotate target",
            is_active=True,
            expires_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "resolve_access_link_anomaly",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "all",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
                "link_id": link.id,
                "resolve_mode": "rotate",
            },
        )
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertFalse(link.is_active)
        self.assertIsNotNone(link.revoked_at)

        dashboard_response = self.client.get(
            "/admin/basetrue-insights/",
            {
                "billing_tenant": "default",
                "billing_client": "profiled_client",
            },
        )
        self.assertEqual(dashboard_response.status_code, 200)
        history_rows = dashboard_response.context["contract_billing_dashboard"]["anomaly_resolution_history"]
        self.assertTrue(any(row.get("action") == "Link Rotated" for row in history_rows))

    def test_run_billing_operational_automation_executes_rotation_retry_and_health_alert(self):
        target_link = ContractBillingAccessLink.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            window_days=30,
            label="Automation rotate target",
            is_active=True,
            use_count=30,
            expires_at=timezone.now() + timedelta(hours=10),
        )
        transient_notification = ContractBillingNotification.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            channel="invoice_email",
            recipient="billing@example.com",
            subject="Transient failure",
            body="Body",
            status="failed",
            last_error="Temporary timeout from upstream SMTP",
        )
        for index in range(8):
            ContractBillingNotification.objects.create(
                tenant_key="default",
                client_key="profiled_client",
                channel="invoice_email",
                recipient=f"policy{index}@example.com",
                subject="Policy failure",
                body="Body",
                status="failed",
                last_error="Policy blocked by receiving gateway",
            )

        response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "run_billing_operational_automation",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "all",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
            },
        )
        self.assertEqual(response.status_code, 302)

        target_link.refresh_from_db()
        self.assertFalse(target_link.is_active)
        self.assertIsNotNone(target_link.revoked_at)
        self.assertTrue(
            ContractBillingAccessLink.objects.filter(
                tenant_key="default",
                client_key="profiled_client",
                label="Automation rotate target",
            ).exclude(id=target_link.id).exists()
        )

        transient_notification.refresh_from_db()
        self.assertGreaterEqual(transient_notification.retry_count, 1)

        self.assertTrue(
            ContractBillingNotification.objects.filter(
                tenant_key="default",
                client_key="profiled_client",
                channel="billing_health",
            ).exists()
        )

    def test_notification_retry_endpoint_delivers_notification(self):
        notification = ContractBillingNotification.objects.create(
            tenant_key="default",
            client_key="profiled_client",
            recipient="billing@example.com",
            subject="Retry me",
            body="Contract billing retry",
            status="failed",
        )
        response = self.client.get(
            f"/admin/insights-contract-billing-notifications/?action=retry&notification_id={notification.id}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        notification.refresh_from_db()
        self.assertEqual(notification.status, "sent")
        self.assertEqual(notification.retry_count, 1)

    def test_billing_job_queue_and_process_workflow(self):
        queue_response = self.client.get(
            "/admin/insights-contract-billing-jobs-queue/?tenant=default&client=profiled_client&job_type=billing_cycle&window_days=30"
        )
        self.assertEqual(queue_response.status_code, 200)
        queue_data = queue_response.json()
        self.assertTrue(queue_data["queued"])
        self.assertTrue(ContractBillingJob.objects.filter(id=queue_data["job_id"]).exists())

        process_response = self.client.get("/admin/insights-contract-billing-jobs-process/?limit=10")
        self.assertEqual(process_response.status_code, 200)
        process_data = process_response.json()
        self.assertGreaterEqual(process_data["processed_count"], 1)
        self.assertTrue(ContractBillingNotification.objects.filter(client_key="profiled_client").exists())

    def test_queued_operational_automation_job_processes_successfully(self):
        queue_response = self.client.post(
            "/admin/basetrue-insights/",
            {
                "billing_console_action": "queue_billing_operational_automation",
                "billing_tenant": "default",
                "billing_client": "profiled_client",
                "billing_link_tenant": "default",
                "billing_link_client": "profiled_client",
                "billing_link_status": "all",
                "billing_link_expires": "all",
                "billing_link_sort": "newest",
            },
        )
        self.assertEqual(queue_response.status_code, 302)

        job = ContractBillingJob.objects.filter(job_type="automation").order_by("-created_at").first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "pending")

        process_response = self.client.get("/admin/insights-contract-billing-jobs-process/?limit=10")
        self.assertEqual(process_response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, "completed")
        self.assertIn("rotations", job.result_payload)
        self.assertIn("retries", job.result_payload)
        self.assertIn("health_notifications", job.result_payload)

    def test_run_billing_automation_management_command_queues_and_processes_job(self):
        output = StringIO()
        call_command(
            "run_billing_automation",
            "--tenant=default",
            "--client=profiled_client",
            "--limit=25",
            stdout=output,
        )

        job = ContractBillingJob.objects.filter(job_type="automation").order_by("-created_at").first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "completed")
        self.assertIn("Queued billing automation job", output.getvalue())
        self.assertIn("Processed job", output.getvalue())

    def test_run_billing_automation_management_command_queue_only(self):
        output = StringIO()
        call_command(
            "run_billing_automation",
            "--tenant=default",
            "--client=profiled_client",
            "--queue-only",
            stdout=output,
        )

        job = ContractBillingJob.objects.filter(job_type="automation").order_by("-created_at").first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "pending")
        self.assertIn("Queued billing automation job", output.getvalue())
        self.assertNotIn("Processed job", output.getvalue())

    def test_tenant_scoped_profile_defaults_are_isolated(self):
        response = self.client.get(
            "/admin/insights-retrospective-export/?period=monthly&format=json&tenant=tenant_beta&client=profiled_client"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertIn("schema_roadmap_ref", data)

    def test_usage_analytics_can_filter_by_tenant(self):
        self.client.get(
            "/admin/insights-retrospective-negotiate/?tenant=tenant_beta&client=profiled_client"
        )
        response = self.client.get(
            "/admin/insights-contract-usage-analytics/?window_days=30&tenant=tenant_beta"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["tenant_key"], "tenant_beta")
        self.assertGreaterEqual(data["total_events"], 1)

    def test_negotiation_endpoint_exposes_concierge_payload(self):
        response = self.client.get(
            "/admin/insights-retrospective-negotiate/?schema_version=lts&from_version=1.0.0&client=legacy_csv_bridge&capabilities=legacy_only&strict_payload_shape=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("recommendation", data)
        self.assertIn("upgrade_paths", data)
        self.assertIn("diff_links", data)
        self.assertIn("contract_lifecycle_states", data)
        self.assertIn("compatibility_matrix", data)
        self.assertIn("alias_resolution", data)
        self.assertIn("strict_shaping_guarantees", data)

        self.assertEqual(data["alias_resolution"]["schema_version"]["provided"], "lts")
        self.assertEqual(data["alias_resolution"]["schema_version"]["resolved"], "1.0.0")
        self.assertEqual(data["recommendation"]["selected_version"], "1.0.0")
        self.assertTrue(data["strict_shaping_guarantees"]["supported"])

    def test_negotiation_endpoint_strict_conflict_returns_400(self):
        response = self.client.get(
            "/admin/insights-retrospective-negotiate/?capabilities=legacy_only,roadmap_ref&strict_negotiation=1"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()

        self.assertEqual(data["error"], "No compatible schema_version for strict negotiation")
        self.assertIn("compatibility_matrix", data)
        self.assertIn("version_aliases", data)


class ContractMlasBtifRoutingTests(TestCase):
    REGRESSION_MARKER = "BTPE-ROUTING-CONTRACT-REGRESSION"
    SPEC_REFERENCES = (
        "docs/architecture/mlas_btif_canonical_spec.md",
        "docs/architecture/mlas_btif_implementation_schemas.md",
        "docs/operations/mlas_btif_validation_checklist.md",
    )

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin_user = user_model.objects.create_superuser(
            username="mlas_contract_admin",
            email="mlas_contract_admin@example.com",
            password="password12345",
        )

        cls.post_statistics_preset = SemanticPreset.objects.create(
            name="post.purple.statistics",
            phase="post",
            color_primary="purple",
            metaphor="mycelium",
            mlas_subject="math",
            mlas_branch="sacp",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=500,
            industry_super_sector="financials",
            industry_sector="banking",
            industry_group="financial-analytics",
            industry_sub_industry="quant-finance",
            ui_category="customer",
        )

        cls.create_foundation_preset = SemanticPreset.objects.create(
            name="create.red.math",
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            mlas_subject="math",
            mlas_branch="base",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=100,
            industry_super_sector="financials",
            industry_sector="banking",
            industry_group="analytics",
            industry_sub_industry="quant",
            ui_category="operations",
        )

        cls.work_history_preset = SemanticPreset.objects.create(
            name="work.pink.history",
            phase="work",
            color_primary="pink",
            metaphor="botanist",
            mlas_subject="history",
            mlas_branch="hist",
            mlas_term="timeline",
            mlas_meta=None,
            dewey_code=900,
            industry_super_sector="industrials",
            industry_sector="ops",
            industry_group="execution",
            industry_sub_industry="delivery",
            ui_category="delivery",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def _create_slide(self, title, ui_category=None):
        return Slide.objects.create(
            title=title,
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            mlas_subject="language",
            mlas_branch="ednp",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=100,
            industry_super_sector="communications",
            industry_sector="media",
            industry_group="publishing",
            industry_sub_industry="digital",
            ui_category=ui_category,
            phase_resolved="create",
            ui_category_resolved="operations",
            layout_archetype="matrix",
            component_pack="foundational-pack",
            nav_group="foundations",
            page_signature="narrative",
        )

    def _assert_spec_references_exist(self):
        repo_root = Path(__file__).resolve().parents[1]
        for rel_path in self.SPEC_REFERENCES:
            self.assertTrue(
                (repo_root / rel_path).exists(),
                msg=(
                    f"Contract violation: missing contract reference {rel_path}. "
                    f"Regression marker: {self.REGRESSION_MARKER}."
                ),
            )

    def test_contract_preset_application_deterministic(self):
        self._assert_spec_references_exist()

        slide_a = self._create_slide("Contract Preset Deterministic A")
        slide_b = self._create_slide("Contract Preset Deterministic B", ui_category="operations")
        url_a = f"/contracts/slides/{slide_a.id}/apply-preset/"
        url_b = f"/contracts/slides/{slide_b.id}/apply-preset/"

        first = self.client.post(
            url_a,
            data={"preset": self.post_statistics_preset.name},
            content_type="application/json",
        )
        second = self.client.post(
            url_a,
            data={"preset": self.post_statistics_preset.name},
            content_type="application/json",
        )
        control = self.client.post(
            url_b,
            data={"preset": self.post_statistics_preset.name},
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(control.status_code, 200)

        payload_first = first.json()
        payload_second = second.json()
        payload_control = control.json()

        self.assertEqual(
            payload_first,
            payload_second,
            msg=(
                "Contract violation: preset application is not idempotent. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        routing_fields = [
            "phase_resolved",
            "color_primary",
            "metaphor",
            "applied_preset",
        ]
        for field_name in routing_fields:
            self.assertEqual(
                payload_first[field_name],
                payload_control[field_name],
                msg=(
                    f"Contract violation: routing drift on {field_name} from prior state. "
                    f"Regression marker: {self.REGRESSION_MARKER}."
                ),
            )

        self.assertEqual(
            payload_first["phase_resolved"],
            "post",
            msg="Contract violation: phase invariant failed (expected post).",
        )
        self.assertEqual(
            payload_first["color_primary"],
            "purple",
            msg="Contract violation: phase -> color invariant failed for post/sacp.",
        )
        self.assertEqual(
            payload_first["metaphor"],
            "mycelium",
            msg="Contract violation: phase -> metaphor invariant failed for post.",
        )

        self.assertEqual(payload_first["mlas"]["subject"], "math")
        self.assertEqual(payload_first["mlas"]["branch"], "sacp")
        self.assertEqual(payload_first["dewey"]["code"], 500)
        self.assertEqual(
            payload_first["industry"]["super_sector"],
            "financials",
            msg="Contract violation: MLAS -> Dewey -> industry chain was not preserved.",
        )

        self.assertEqual(payload_first["ui"]["layout_archetype"], "journey")
        self.assertEqual(payload_first["ui"]["component_pack"], "narrative-pack")
        self.assertEqual(payload_first["dewey"]["nav_group"], "information")
        self.assertEqual(payload_first["industry"]["page_signature"], "analytical")

        self.assertIsNotNone(payload_first["phase_resolved"])
        self.assertIsNotNone(payload_first["color_primary"])
        self.assertIsNotNone(payload_first["metaphor"])
        self.assertIsNotNone(payload_first["ui"]["layout_archetype"])
        self.assertIsNotNone(payload_first["ui"]["component_pack"])

    def test_contract_deep_pack_requires_meta_term(self):
        self._assert_spec_references_exist()

        slide = self._create_slide("Contract Deep Pack")
        url = f"/contracts/slides/{slide.id}/apply-preset/"

        missing_meta = self.client.post(
            url,
            data={
                "preset": self.work_history_preset.name,
                "component_pack": "deep-pack",
                "mlas_meta": None,
            },
            content_type="application/json",
        )
        self.assertEqual(
            missing_meta.status_code,
            400,
            msg="Contract violation: deep-pack accepted a payload without mlas_meta.",
        )
        self.assertIn("mlas_meta is required", missing_meta.json()["detail"])

        with_meta = self.client.post(
            url,
            data={
                "preset": self.work_history_preset.name,
                "component_pack": "deep-pack",
                "mlas_meta": "evolution",
            },
            content_type="application/json",
        )
        self.assertEqual(with_meta.status_code, 200)
        payload = with_meta.json()

        self.assertEqual(
            payload["ui"]["component_pack"],
            "deep-pack",
            msg="Contract violation: deep-pack request downgraded silently.",
        )
        self.assertEqual(
            payload["mlas"]["meta"],
            "evolution",
            msg="Contract violation: deep-pack meta-term was not preserved.",
        )
        self.assertEqual(
            payload["metaphor"],
            "botanist",
            msg="Contract violation: deep-pack semantics require botanist metaphor.",
        )

    def test_contract_work_phase_category_resolution(self):
        self._assert_spec_references_exist()

        default_slide = self._create_slide("Contract Work Default")
        override_slide = self._create_slide("Contract Work Executive", ui_category="executive")

        default_url = f"/contracts/slides/{default_slide.id}/apply-preset/"
        override_url = f"/contracts/slides/{override_slide.id}/apply-preset/"

        default_response = self.client.post(
            default_url,
            data={"preset": self.work_history_preset.name},
            content_type="application/json",
        )
        inherited_override = self.client.post(
            override_url,
            data={"preset": self.work_history_preset.name},
            content_type="application/json",
        )
        explicit_override = self.client.post(
            default_url,
            data={"preset": self.work_history_preset.name, "ui_category": "executive"},
            content_type="application/json",
        )

        self.assertEqual(default_response.status_code, 200)
        self.assertEqual(inherited_override.status_code, 200)
        self.assertEqual(explicit_override.status_code, 200)

        default_payload = default_response.json()
        inherited_payload = inherited_override.json()
        explicit_payload = explicit_override.json()

        self.assertEqual(
            default_payload["phase_resolved"],
            "work",
            msg="Contract violation: work phase routing did not resolve to work.",
        )
        self.assertEqual(
            default_payload["ui"]["category_resolved"],
            "delivery",
            msg="Contract violation: work phase did not default to delivery.",
        )

        self.assertEqual(
            inherited_payload["ui"]["category_resolved"],
            "executive",
            msg="Contract violation: explicit executive category override was not respected.",
        )
        self.assertEqual(
            explicit_payload["ui"]["category_resolved"],
            "executive",
            msg="Contract violation: request-scoped executive override was not respected.",
        )

        self.assertNotEqual(
            default_payload["ui"]["category_resolved"],
            "executive",
            msg="Contract violation: work phase inferred executive without explicit metadata.",
        )
        self.assertNotIn(
            default_payload["ui"]["category_resolved"],
            {"customer", "operations"},
            msg="Contract violation: work phase resolved to forbidden categories.",
        )

    def test_contract_preset_catalog_is_deterministic(self):
        self._assert_spec_references_exist()

        first = self.client.get("/contracts/presets/")
        second = self.client.get("/contracts/presets/")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        payload_first = first.json()
        payload_second = second.json()
        self.assertEqual(
            payload_first,
            payload_second,
            msg=(
                "Contract violation: preset catalog endpoint is non-deterministic. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        self.assertIn("presets", payload_first)
        self.assertIsInstance(payload_first["presets"], list)
        self.assertGreaterEqual(
            len(payload_first["presets"]),
            2,
            msg=(
                "Contract violation: preset catalog must expose canonical preset entries. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        for item in payload_first["presets"]:
            self.assertIn("name", item)
            self.assertIn("phase", item)

        names = [item["name"] for item in payload_first["presets"]]
        self.assertEqual(
            len(names),
            len(set(names)),
            msg=(
                "Contract violation: preset catalog contains duplicate preset names. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        phase_order = {"create": 0, "post": 1, "work": 2}
        observed = [(item["name"], item["phase"]) for item in payload_first["presets"]]
        expected = sorted(observed, key=lambda pair: (phase_order.get(pair[1], 99), pair[0]))
        self.assertEqual(
            observed,
            expected,
            msg=(
                "Contract violation: preset catalog ordering drifted from deterministic contract ordering. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_preset_catalog_exposes_bundles_and_executive_modes(self):
        self._assert_spec_references_exist()

        response = self.client.get("/contracts/presets/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        names = {item["name"] for item in payload.get("presets", [])}
        expected_aliases = {
            "create.foundation",
            "post.storyline",
            "work.execution",
            "executive.summary",
            "executive.pipeline",
            "executive.overview",
        }
        missing = expected_aliases - names
        self.assertFalse(
            missing,
            msg=(
                f"Contract violation: missing preset aliases {sorted(missing)}. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_bundle_generator_sequence_is_deterministic(self):
        self._assert_spec_references_exist()

        source_slide = self._create_slide("Contract Bundle Generator")
        url = f"/contracts/slides/{source_slide.id}/generate-bundle/"

        first = self.client.post(url, data={"bundle": "bundle.foundation.triad"}, content_type="application/json")
        second = self.client.post(url, data={"bundle": "bundle.foundation.triad"}, content_type="application/json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        payload = first.json()
        payload_second = second.json()

        self.assertEqual(
            payload["bundle"],
            "bundle.foundation.triad",
            msg=(
                "Contract violation: bundle name mismatch on generated sequence. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )
        self.assertEqual(
            len(payload.get("generated", [])),
            3,
            msg=(
                "Contract violation: foundation bundle must generate exactly 3 slides. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        first_layouts = [item["slide"]["ui"]["layout_archetype"] for item in payload["generated"]]
        self.assertEqual(
            first_layouts,
            ["matrix", "journey", "pipeline"],
            msg=(
                "Contract violation: bundle layout sequencing drifted from matrix->journey->pipeline. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

        second_layouts = [item["slide"]["ui"]["layout_archetype"] for item in payload_second["generated"]]
        self.assertEqual(
            second_layouts,
            first_layouts,
            msg=(
                "Contract violation: bundle generation is non-deterministic across runs. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_bundle_catalog_exposes_preview_metadata(self):
        self._assert_spec_references_exist()

        response = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        bundles = payload.get("bundles", [])
        foundation = next((item for item in bundles if item["name"] == "bundle.foundation.triad"), None)

        self.assertIsNotNone(
            foundation,
            msg=(
                "Contract violation: foundation bundle missing from bundle catalog. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )
        self.assertEqual(foundation["slide_count"], 3)
        self.assertEqual(foundation["phase_distribution"], {"create": 1, "post": 1, "work": 1})
        self.assertEqual(foundation["layout_distribution"], {"matrix": 1, "journey": 1, "pipeline": 1})
        self.assertTrue(foundation["supports_inversion"])

    def test_contract_bundle_generator_supports_executive_inversion(self):
        self._assert_spec_references_exist()

        source_slide = self._create_slide("Contract Inverted Bundle")
        response = self.client.post(
            f"/contracts/slides/{source_slide.id}/generate-bundle/",
            data={"bundle": "bundle.foundation.triad", "inversion": "executive"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        categories = [item["slide"]["ui"]["category_resolved"] for item in payload.get("generated", [])]
        self.assertEqual(
            categories,
            ["executive", "executive", "executive"],
            msg=(
                "Contract violation: executive inversion did not propagate across the bundle. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_bundle_preview_mode_does_not_persist_rows(self):
        self._assert_spec_references_exist()

        source_slide = self._create_slide("Contract Preview Bundle")
        before_count = Slide.objects.count()
        response = self.client.post(
            f"/contracts/slides/{source_slide.id}/generate-bundle/",
            data={"bundle": "bundle.foundation.triad", "persist_generated": False},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["persist_generated"])
        self.assertEqual(
            Slide.objects.count(),
            before_count,
            msg=(
                "Contract violation: preview bundle generation persisted slide rows. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_persisted_bundle_appears_in_catalog(self):
        self._assert_spec_references_exist()

        create_response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-saved",
                "label": "Contract Saved",
                "family": "custom.contract",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertIn(create_response.status_code, {200, 201})

        catalog = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(catalog.status_code, 200)
        names = {item["name"] for item in catalog.json().get("bundles", [])}
        self.assertIn(
            "custom.bundle.contract-saved",
            names,
            msg=(
                "Contract violation: persisted bundle missing from bundle catalog. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_persisted_bundle_catalog_is_user_scoped(self):
        self._assert_spec_references_exist()

        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.private-contract",
                "label": "Private Contract",
                "family": "custom.private",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        other_user = get_user_model().objects.create_user(
            username="contract_other_user",
            email="contract_other_user@example.com",
            password="password12345",
        )
        self.client.force_login(other_user)
        response = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json().get("bundles", [])}
        self.assertNotIn(
            "custom.bundle.private-contract",
            names,
            msg=(
                "Contract violation: persisted bundle leaked across user boundaries. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_bundle_history_tracks_immutable_revisions(self):
        self._assert_spec_references_exist()

        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-history",
                "label": "Contract History v1",
                "family": "custom.contract",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-history",
                "label": "Contract History v2",
                "family": "custom.contract",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        response = self.client.get("/contracts/preset-bundles/custom.bundle.contract-history/history/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(
            payload["bundle"]["current_revision"]["revision_number"],
            2,
            msg=(
                "Contract violation: current bundle revision metadata drifted. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )
        self.assertEqual(
            [item["revision_number"] for item in payload["history"]],
            [2, 1],
            msg=(
                "Contract violation: bundle revision history is not immutable or ordered latest-first. "
                f"Regression marker: {self.REGRESSION_MARKER}."
            ),
        )

    def test_contract_bundle_share_grants_visibility_without_owner_transfer(self):
        self._assert_spec_references_exist()

        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-shared",
                "label": "Contract Shared",
                "family": "custom.contract",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        collaborator = get_user_model().objects.create_user(
            username="contract_collaborator",
            email="contract_collaborator@example.com",
            password="password12345",
        )
        share_response = self.client.post(
            "/contracts/preset-bundles/custom.bundle.contract-shared/shares/",
            data={"username": collaborator.username, "permission": "view"},
            content_type="application/json",
        )
        self.assertIn(share_response.status_code, {200, 201})

        self.client.force_login(collaborator)
        catalog = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(catalog.status_code, 200)
        shared_bundle = next((item for item in catalog.json().get("bundles", []) if item["name"] == "custom.bundle.contract-shared"), None)
        self.assertIsNotNone(shared_bundle)
        self.assertEqual(shared_bundle["access_role"], "view")

    def test_contract_bundle_compare_exposes_revision_delta_shape(self):
        self._assert_spec_references_exist()

        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-compare",
                "label": "Contract Compare v1",
                "family": "custom.contract",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.contract-compare",
                "label": "Contract Compare v2",
                "family": "custom.contract.updated",
                "sequence": ["post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        response = self.client.get("/contracts/preset-bundles/custom.bundle.contract-compare/compare/?from=1&to=2")
        self.assertEqual(response.status_code, 200)
        payload = response.json().get("compare", {})
        self.assertIn("changes", payload)
        self.assertIn("sequence", payload)
        self.assertIn("distribution", payload)
        self.assertIn("executive_projection", payload)
