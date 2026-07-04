from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from baseture_engine.models import IndustryProfile, TierDefinition
from baseture_engine.pattern_rules import (
    INDUSTRY_RULES,
    MLAS_PATTERN_RULES,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed BaseTrue Pattern Engine with initial industry profiles and tier definitions"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🌱 Starting BTPE data seeding..."))

        # Get or create superuser for created_by
        admin_user, created = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True, "is_staff": True}
        )
        if created:
            admin_user.set_password("admin")
            admin_user.save()
            self.stdout.write(
                self.style.WARNING("⚠️  Created admin user (username: admin, password: admin)")
            )

        # Seed IndustryProfile records
        self.stdout.write("\n📋 Seeding IndustryProfile records...")
        industry_count = 0

        for industry_key, industry_config in INDUSTRY_RULES.items():
            profile, created = IndustryProfile.objects.get_or_create(
                industry=industry_key,
                defaults={
                    "name": industry_config.get("name", industry_key.title()),
                    "description": industry_config.get("description", f"{industry_key} industry"),
                    "required_components": industry_config.get("required_components", {}),
                    "pattern_constraints": industry_config.get("pattern_constraints", {}),
                },
            )
            if created:
                self.stdout.write(f"  ✅ Created IndustryProfile: {industry_key}")
                industry_count += 1
            else:
                self.stdout.write(f"  ⏭️  IndustryProfile already exists: {industry_key}")

        self.stdout.write(
            self.style.SUCCESS(f"✅ Seeded {industry_count} IndustryProfile records\n")
        )

        # Seed TierDefinition records for each MLAS color × industry × tier_level combination
        self.stdout.write("📊 Seeding TierDefinition records...")
        tier_count = 0
        tier_level_choices = [1, 2, 3]

        for mlas_color, mlas_config in MLAS_PATTERN_RULES.items():
            for industry_key, industry_config in INDUSTRY_RULES.items():
                for tier_level in tier_level_choices:
                    tier_def, created = TierDefinition.objects.get_or_create(
                        tier_level=tier_level,
                        mlas_color=mlas_color,
                        industry_id=IndustryProfile.objects.get(industry=industry_key).id,
                        defaults={
                            "name": f"{mlas_config['name']} - {mlas_color} Tier {tier_level}",
                            "description": f"Tier {tier_level} {mlas_config['name']} pattern for {industry_key}",
                            "pattern_type": mlas_config.get("pattern_type", "narrative"),
                            "complexity": min(tier_level, 3),
                            "required_fields": {
                                "seed_input": True,
                                "mlas_color": mlas_color,
                                "industry": industry_key,
                                "tier_level": tier_level,
                            },
                            "behaviors": mlas_config.get("behaviors", []),
                            "created_by": admin_user,
                        },
                    )
                    if created:
                        tier_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {tier_count} TierDefinition records\n"))

        # Summary
        total_industries = IndustryProfile.objects.count()
        total_tiers = TierDefinition.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 BTPE data seeding complete!"
                f"\n   • IndustryProfile records: {total_industries}"
                f"\n   • TierDefinition records: {total_tiers}"
                f"\n   • Tier combination: {len(MLAS_PATTERN_RULES)} colors × {len(INDUSTRY_RULES)} industries × 3 tiers"
            )
        )
