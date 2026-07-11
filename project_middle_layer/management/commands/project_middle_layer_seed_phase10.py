import json

from django.core.management.base import BaseCommand

from project_middle_layer.models import (
    ExternalAgent,
    MarketplaceItem,
    MarketplaceVersion,
    SemanticPlugin,
    SemanticExtension,
    SemanticRole,
    SemanticUserProfile,
)
from users.models import User


PHASE10_CAPABILITIES = [
    "manage.marketplace",
    "manage.plugins",
    "manage.extensions",
    "gateway.inspect",
    "gateway.dispatch",
    "btif.interop",
    "manage.external_agents",
    "sync.cross_platform",
]


class Command(BaseCommand):
    help = "Seed deterministic Phase 10 role capabilities and demo platformization records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="",
            help="Optional username to attach seeded default role to semantic profile.",
        )
        parser.add_argument(
            "--skip-roles",
            action="store_true",
            help="Skip role/capability seed.",
        )
        parser.add_argument(
            "--skip-demo-data",
            action="store_true",
            help="Skip demo marketplace/plugin/extension/external-agent seed.",
        )

    def handle(self, *args, **options):
        summary = {
            "roles": {},
            "demo_data": {},
            "profile_assignment": {},
        }

        if not options.get("skip_roles"):
            operator_role, operator_created = SemanticRole.objects.update_or_create(
                slug="phase10-platform-operator",
                defaults={
                    "name": "Phase 10 Platform Operator",
                    "capabilities": PHASE10_CAPABILITIES,
                },
            )
            summary["roles"]["phase10-platform-operator"] = {
                "created": operator_created,
                "capability_count": len(operator_role.capabilities or []),
            }

            reviewer_role, reviewer_created = SemanticRole.objects.update_or_create(
                slug="phase10-platform-reviewer",
                defaults={
                    "name": "Phase 10 Platform Reviewer",
                    "capabilities": [
                        "gateway.inspect",
                        "btif.interop",
                        "sync.cross_platform",
                    ],
                },
            )
            summary["roles"]["phase10-platform-reviewer"] = {
                "created": reviewer_created,
                "capability_count": len(reviewer_role.capabilities or []),
            }

            username = (options.get("username") or "").strip()
            if username:
                user = User.objects.filter(username=username).first()
                if user:
                    SemanticUserProfile.objects.update_or_create(
                        user=user,
                        defaults={"default_role": operator_role},
                    )
                    summary["profile_assignment"] = {
                        "username": username,
                        "assigned_role": operator_role.slug,
                        "status": "assigned",
                    }
                else:
                    summary["profile_assignment"] = {
                        "username": username,
                        "status": "user_not_found",
                    }

        if not options.get("skip_demo_data"):
            item, item_created = MarketplaceItem.objects.update_or_create(
                slug="semantic-starter-plugin-pack",
                defaults={
                    "name": "Semantic Starter Plugin Pack",
                    "item_type": "plugin",
                    "current_version": "1.1.0",
                    "metadata": {
                        "description": "Starter marketplace package for Phase 10 smoke testing.",
                        "seeded": True,
                    },
                    "is_active": True,
                },
            )
            version_100, version_100_created = MarketplaceVersion.objects.update_or_create(
                item=item,
                version="1.0.0",
                defaults={
                    "changelog": "Initial public release",
                    "compatibility": {"min_project_middle_layer": "0.0.1"},
                    "dependency_slugs": [],
                    "download_url": "https://example.com/marketplace/semantic-starter-plugin-pack/1.0.0",
                },
            )
            version_110, version_110_created = MarketplaceVersion.objects.update_or_create(
                item=item,
                version="1.1.0",
                defaults={
                    "changelog": "Adds gateway and cross-sync utility hooks",
                    "compatibility": {
                        "min_project_middle_layer": "0.0.1",
                        "notes": "Validated against strict-permission mode",
                    },
                    "dependency_slugs": [],
                    "download_url": "https://example.com/marketplace/semantic-starter-plugin-pack/1.1.0",
                },
            )

            plugin, plugin_created = SemanticPlugin.objects.update_or_create(
                slug="semantic-observability-plugin",
                defaults={
                    "name": "Semantic Observability Plugin",
                    "plugin_type": "agent",
                    "entrypoint": "project_middle_layer.plugins.semantic_observability",
                    "capabilities": ["gateway.inspect", "sync.cross_platform"],
                    "version": "0.1.0",
                    "enabled": False,
                    "metadata": {"seeded": True},
                },
            )

            extension, extension_created = SemanticExtension.objects.update_or_create(
                slug="semantic-core-patch",
                defaults={
                    "name": "Semantic Core Patch",
                    "version": "0.1.0",
                    "schema_patch": {"add_fields": ["phase10_marker"]},
                    "rules_patch": {"enforce": ["deterministic_inputs"]},
                },
            )

            agent, agent_created = ExternalAgent.objects.update_or_create(
                slug="partner-sandbox-agent",
                defaults={
                    "name": "Partner Sandbox Agent",
                    "endpoint": "https://example.com/agents/partner-sandbox",
                    "capabilities": ["analyze", "summarize"],
                    "auth_token": "",
                    "status": "active",
                    "metadata": {"seeded": True, "sandbox": True},
                },
            )

            summary["demo_data"] = {
                "marketplace_item": {"slug": item.slug, "created": item_created},
                "marketplace_versions": [
                    {"version": version_100.version, "created": version_100_created},
                    {"version": version_110.version, "created": version_110_created},
                ],
                "plugin": {"slug": plugin.slug, "created": plugin_created},
                "extension": {"slug": extension.slug, "created": extension_created},
                "external_agent": {"slug": agent.slug, "created": agent_created},
            }

        self.stdout.write(json.dumps(summary, sort_keys=True))
