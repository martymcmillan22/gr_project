import json
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.template import Context, Template
from django.test import SimpleTestCase

from platform_core.models import QuadrantUsageEvent
from platform_core.views import quadrant_heatmap_view, quadrant_overlay_view, quadrant_redirect_view, quadrant_route_view

from platform_core.resolvers.quadrant import (
    AM_DOMAINS,
    PM_DOMAINS,
    get_current_hour,
    is_pm,
    resolve_domain,
    resolve_url,
)
from platform_core.resolvers.quadrant_inversion import resolve_inversion_target


class QuadrantResolverTests(SimpleTestCase):
    def test_get_current_hour_uses_12_hour_clock(self):
        with patch("platform_core.resolvers.quadrant.timezone.localtime") as localtime:
            localtime.return_value = type("MockNow", (), {"hour": 0})()
            self.assertEqual(get_current_hour(), 12)

    def test_is_pm_reads_server_time(self):
        with patch("platform_core.resolvers.quadrant.timezone.localtime") as localtime:
            localtime.return_value = type("MockNow", (), {"hour": 13})()
            self.assertTrue(is_pm())

    def test_resolve_domain_uses_am_map_when_am(self):
        self.assertEqual(resolve_domain(hour=1, pm=False), AM_DOMAINS[1])
        self.assertEqual(resolve_domain(hour=12, pm=False), AM_DOMAINS[12])

    def test_resolve_domain_uses_pm_map_when_pm(self):
        self.assertEqual(resolve_domain(hour=1, pm=True), PM_DOMAINS[1])
        self.assertEqual(resolve_domain(hour=12, pm=True), PM_DOMAINS[12])

    def test_resolve_url_matches_project_routes(self):
        self.assertEqual(resolve_url(hour=1, pm=False), "/center/grid/bos/")
        self.assertEqual(resolve_url(hour=1, pm=True), "/domain/grid/bos-domain/")

    def test_compartment_12_inversion_am_to_pm(self):
        target_hour, target_pm, is_active = resolve_inversion_target(12, False)
        self.assertEqual(target_hour, 1)
        self.assertTrue(target_pm)
        self.assertTrue(is_active)

    def test_compartment_12_inversion_pm_to_am(self):
        target_hour, target_pm, is_active = resolve_inversion_target(12, True)
        self.assertEqual(target_hour, 1)
        self.assertFalse(target_pm)
        self.assertTrue(is_active)

    def test_non_hinge_hour_has_no_inversion(self):
        target_hour, target_pm, is_active = resolve_inversion_target(6, False)
        self.assertEqual(target_hour, 6)
        self.assertFalse(target_pm)
        self.assertFalse(is_active)


class QuadrantIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_quadrant_route_view_returns_am_route(self):
        request = self.factory.get("/platform-core/quadrant/route/")
        with patch("platform_core.views.get_current_hour", return_value=1), patch("platform_core.views.is_pm", return_value=False):
            response = quadrant_route_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode("utf-8")), {"slug": "bos", "url": "/center/grid/bos/"})

    def test_quadrant_route_view_returns_pm_route(self):
        request = self.factory.get("/platform-core/quadrant/route/")
        with patch("platform_core.views.get_current_hour", return_value=1), patch("platform_core.views.is_pm", return_value=True):
            response = quadrant_route_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode("utf-8")), {"slug": "bos-domain", "url": "/domain/grid/bos-domain/"})

    def test_navigation_truth_guard_routes_12pm_to_center_harvestcrops(self):
        request = self.factory.get("/platform-core/quadrant/route/")
        with patch("platform_core.views.get_current_hour", return_value=12), patch("platform_core.views.is_pm", return_value=True):
            response = quadrant_route_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode("utf-8")),
            {"slug": "harvestcrops", "url": "/center/grid/harvestcrops/"},
        )

    def test_navigation_truth_guard_routes_12am_to_domain_tr(self):
        request = self.factory.get("/platform-core/quadrant/route/")
        with patch("platform_core.views.get_current_hour", return_value=12), patch("platform_core.views.is_pm", return_value=False):
            response = quadrant_route_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode("utf-8")),
            {"slug": "tr", "url": "/domain/grid/tr/"},
        )

    def test_navigation_truth_guard_route_self_heals_if_mapping_drifts(self):
        request = self.factory.get("/platform-core/quadrant/route/")
        with (
            patch("platform_core.views.get_current_hour", return_value=12),
            patch("platform_core.views.is_pm", return_value=True),
            patch("platform_core.views.resolve_domain", return_value="wrong-slug"),
            patch("platform_core.views.resolve_url", return_value="/domain/grid/wrong-slug/"),
        ):
            response = quadrant_route_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode("utf-8")),
            {"slug": "harvestcrops", "url": "/center/grid/harvestcrops/"},
        )

    def test_quadrant_url_template_tag_renders_current_route(self):
        template = Template("{% load quadrant %}{% quadrant_url 1 False %}")
        rendered = template.render(Context({}))

        self.assertEqual(rendered, "/center/grid/bos/")

    def test_quadrant_redirect_view_redirects_to_resolver_output(self):
        request = self.factory.get("/quadrant/")
        with patch("platform_core.views.get_current_hour", return_value=1), patch("platform_core.views.is_pm", return_value=False), patch("platform_core.views.resolve_url", return_value="/center/grid/bos/"):
            response = quadrant_redirect_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/center/grid/bos/")
        self.assertEqual(QuadrantUsageEvent.objects.count(), 1)
        event = QuadrantUsageEvent.objects.get()
        self.assertEqual(event.hour, 1)
        self.assertFalse(event.is_pm)
        self.assertEqual(event.slug, "bos")

    def test_quadrant_redirect_view_logs_pm_event(self):
        request = self.factory.get("/quadrant/")
        with patch("platform_core.views.get_current_hour", return_value=1), patch("platform_core.views.is_pm", return_value=True), patch("platform_core.views.resolve_url", return_value="/domain/grid/bos-domain/"):
            response = quadrant_redirect_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/domain/grid/bos-domain/")
        event = QuadrantUsageEvent.objects.latest("created_at")
        self.assertEqual(event.hour, 1)
        self.assertTrue(event.is_pm)
        self.assertEqual(event.slug, "bos-domain")

    def test_navigation_truth_guard_redirects_12pm_to_center_harvestcrops(self):
        request = self.factory.get("/quadrant/")
        with patch("platform_core.views.get_current_hour", return_value=12), patch("platform_core.views.is_pm", return_value=True):
            response = quadrant_redirect_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/center/grid/harvestcrops/")
        event = QuadrantUsageEvent.objects.latest("created_at")
        self.assertEqual(event.hour, 12)
        self.assertTrue(event.is_pm)
        self.assertEqual(event.slug, "harvestcrops")

    def test_navigation_truth_guard_redirects_12am_to_domain_tr(self):
        request = self.factory.get("/quadrant/")
        with patch("platform_core.views.get_current_hour", return_value=12), patch("platform_core.views.is_pm", return_value=False):
            response = quadrant_redirect_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/domain/grid/tr/")
        event = QuadrantUsageEvent.objects.latest("created_at")
        self.assertEqual(event.hour, 12)
        self.assertFalse(event.is_pm)
        self.assertEqual(event.slug, "tr")

    def test_navigation_truth_guard_redirect_self_heals_if_mapping_drifts(self):
        request = self.factory.get("/quadrant/")
        with (
            patch("platform_core.views.get_current_hour", return_value=12),
            patch("platform_core.views.is_pm", return_value=False),
            patch("platform_core.views.resolve_domain", return_value="wrong-slug"),
            patch("platform_core.views.resolve_url", return_value="/center/grid/wrong-slug/"),
        ):
            response = quadrant_redirect_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/domain/grid/tr/")
        event = QuadrantUsageEvent.objects.latest("created_at")
        self.assertEqual(event.hour, 12)
        self.assertFalse(event.is_pm)
        self.assertEqual(event.slug, "tr")

    def test_quadrant_heatmap_view_returns_am_pm_counts(self):
        QuadrantUsageEvent.objects.create(hour=1, is_pm=False, slug="bos")
        QuadrantUsageEvent.objects.create(hour=1, is_pm=False, slug="bos")
        QuadrantUsageEvent.objects.create(hour=1, is_pm=True, slug="bos-domain")
        QuadrantUsageEvent.objects.create(hour=12, is_pm=True, slug="harvestcrops-domain")

        request = self.factory.get("/quadrant/heatmap/")
        response = quadrant_heatmap_view(request)
        payload = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["am"]["1"], 2)
        self.assertEqual(payload["pm"]["1"], 1)
        self.assertEqual(payload["pm"]["12"], 1)
        self.assertEqual(payload["am"]["12"], 0)

    def test_quadrant_overlay_view_returns_mode_slots_and_usage(self):
        QuadrantUsageEvent.objects.create(hour=1, is_pm=False, slug="bos")
        QuadrantUsageEvent.objects.create(hour=1, is_pm=False, slug="bos")
        QuadrantUsageEvent.objects.create(hour=4, is_pm=False, slug="seedlings")

        request = self.factory.get("/quadrant/overlay/")
        with patch("platform_core.views.get_current_hour", return_value=1), patch("platform_core.views.is_pm", return_value=False):
            response = quadrant_overlay_view(request)

        payload = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["mode"], "am")
        self.assertEqual(payload["active_hour"], 1)
        self.assertIn("inversion", payload)
        self.assertFalse(payload["inversion"]["is_active"])
        self.assertEqual(len(payload["slots"]), 12)
        self.assertEqual(payload["slots"][0]["hour"], 1)
        self.assertEqual(payload["slots"][0]["slug"], "bos")
        self.assertEqual(payload["slots"][0]["usage_count"], 2)
        self.assertTrue(payload["slots"][0]["is_active"])
        self.assertFalse(payload["slots"][0]["is_hinge"])
        self.assertEqual(payload["slots"][3]["hour"], 4)
        self.assertEqual(payload["slots"][3]["usage_count"], 1)

    def test_quadrant_overlay_view_marks_hinge_and_inversion_target(self):
        request = self.factory.get("/quadrant/overlay/")
        with patch("platform_core.views.get_current_hour", return_value=12), patch("platform_core.views.is_pm", return_value=False):
            response = quadrant_overlay_view(request)

        payload = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["inversion"]["is_active"])
        self.assertEqual(payload["inversion"]["source"], {"hour": 12, "mode": "am"})
        self.assertEqual(payload["inversion"]["target"]["hour"], 1)
        self.assertEqual(payload["inversion"]["target"]["mode"], "pm")
        self.assertEqual(payload["inversion"]["target"]["slug"], "bos-domain")
        self.assertEqual(payload["inversion"]["target"]["url"], "/domain/grid/bos-domain/")

        hinge_slot = next(slot for slot in payload["slots"] if slot["hour"] == 12)
        self.assertTrue(hinge_slot["is_hinge"])
        self.assertTrue(hinge_slot["is_active"])
