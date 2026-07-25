from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from users.models import User

from .models import (
	ConvectionCompartment,
	Industry,
	IndustryGroup,
	LatticeCompartment,
	PIPLifecycle,
	Recycle3Profile,
	SectorTier,
	SubIndustry,
	UserLatticeAssignment,
)
from .pip_state import PIPState, PIPWorkflowService
from .srl import SRLService
from .views import seed_peringram_structure


class PIPViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="pip-user",
			email="pip@example.com",
			password="pass1234",
		)

	def test_dashboard_requires_login(self):
		response = self.client.get(reverse("peringram:dashboard"))
		self.assertEqual(response.status_code, 302)

	def test_dashboard_seeds_sector_and_convection_structure(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("peringram:dashboard"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(IndustryGroup.objects.count(), 16)
		self.assertEqual(Industry.objects.count(), 64)
		self.assertEqual(SubIndustry.objects.count(), 256)
		self.assertEqual(ConvectionCompartment.objects.count(), 24)
		self.assertEqual(LatticeCompartment.objects.count(), 12)
		self.assertEqual(LatticeCompartment.objects.get(index=10).capacity, 1048576)
		self.assertEqual(LatticeCompartment.objects.get(index=11).category, "Philosophy/Ethics")

	def test_isea_helper_computes_100_percent_total(self):
		allocation = Recycle3Profile(
			user=self.user,
			corporation_rnd_pct=Decimal("33.33"),
			people_qcqa_pct=Decimal("33.33"),
			government_infra_pct=Decimal("33.33"),
			isea_pct=Decimal("0.01"),
		)
		allocation.full_clean()
		self.assertEqual(allocation.recycle_total(), Decimal("99.99"))
		self.assertEqual(allocation.total_with_isea(), Decimal("100.00"))

	def test_sector_tier_thresholds(self):
		cases = [
			(("33.33", "33.33", "33.33"), "0.00", SectorTier.MLAS),
			(("33.33", "33.33", "33.33"), "0.01", SectorTier.SEVM),
			(("40.00", "40.00", "40.00"), "0.01", SectorTier.CCPP),
			(("50.00", "50.00", "50.00"), "0.02", SectorTier.DCHD),
		]
		for (corp, people, gov), isea, expected_tier in cases:
			profile = Recycle3Profile(
				user=self.user,
				corporation_rnd_pct=Decimal(corp),
				people_qcqa_pct=Decimal(people),
				government_infra_pct=Decimal(gov),
				isea_pct=Decimal(isea),
			)
			self.assertEqual(profile.calculate_sector_tier(), expected_tier)

	def test_pip_workflow_service_gates_lifecycle_actions(self):
		profile = Recycle3Profile(
			user=self.user,
			corporation_rnd_pct=Decimal("33.33"),
			people_qcqa_pct=Decimal("33.33"),
			government_infra_pct=Decimal("33.33"),
			isea_pct=Decimal("0.01"),
		)
		pip_state = PIPState.from_recycle3(profile)
		self.assertEqual(pip_state.sector_tier, SectorTier.SEVM)
		self.assertTrue(PIPWorkflowService.can_perform_action(PIPLifecycle.IDEA, pip_state))
		self.assertTrue(PIPWorkflowService.can_perform_action(PIPLifecycle.SEED, pip_state))
		self.assertFalse(PIPWorkflowService.can_perform_action(PIPLifecycle.PROJECT, pip_state))
		self.assertFalse(PIPWorkflowService.can_perform_action(PIPLifecycle.ENTERPRISE, pip_state))
		self.assertFalse(pip_state.rr_unlocked)
		self.assertFalse(pip_state.qpu_unlocked)

	def test_domain_ordering_for_key_groups(self):
		self.client.force_login(self.user)
		self.client.get(reverse("peringram:dashboard"))
		self.assertEqual(IndustryGroup.objects.get(code=1).name, "Math")
		self.assertEqual(IndustryGroup.objects.get(code=2).name, "Language")
		self.assertEqual(IndustryGroup.objects.get(code=3).name, "Arts")
		self.assertEqual(IndustryGroup.objects.get(code=4).name, "Science")
		self.assertEqual(IndustryGroup.objects.get(code=10).name, "Geology")

	def test_srl_service_assigns_deterministic_compartment(self):
		seed_peringram_structure()
		compartment = SRLService.assign_compartment(self.user)
		expected_index = ((self.user.id - 1) % 12) + 1
		self.assertEqual(compartment.index, expected_index)
		self.assertEqual(UserLatticeAssignment.objects.filter(user=self.user).count(), 1)
		# Re-assigning the same user returns the same compartment (idempotent).
		again = SRLService.assign_compartment(self.user)
		self.assertEqual(again.index, expected_index)
		self.assertEqual(UserLatticeAssignment.objects.filter(user=self.user).count(), 1)

	def test_srl_boost_bumps_tier_only_at_or_above_half(self):
		seed_peringram_structure()
		profile = Recycle3Profile(
			user=self.user,
			corporation_rnd_pct=Decimal("33.33"),
			people_qcqa_pct=Decimal("33.33"),
			government_infra_pct=Decimal("33.33"),
			isea_pct=Decimal("0.00"),
		)
		# Base tier with no compartment is MLAS (isea < 0.01).
		self.assertEqual(profile.calculate_sector_tier(), SectorTier.MLAS)

		past = LatticeCompartment.objects.get(index=1)  # time_frame=past, boost=0
		present_past = LatticeCompartment.objects.get(index=2)  # boost=0.25
		present_future = LatticeCompartment.objects.get(index=3)  # boost=0.5
		future = LatticeCompartment.objects.get(index=4)  # boost=1

		self.assertEqual(profile.calculate_sector_tier(past), SectorTier.MLAS)
		self.assertEqual(profile.calculate_sector_tier(present_past), SectorTier.MLAS)
		self.assertEqual(profile.calculate_sector_tier(present_future), SectorTier.SEVM)
		self.assertEqual(profile.calculate_sector_tier(future), SectorTier.SEVM)

	def test_pip_state_includes_territory_and_time_slot(self):
		seed_peringram_structure()
		profile = Recycle3Profile(
			user=self.user,
			corporation_rnd_pct=Decimal("33.33"),
			people_qcqa_pct=Decimal("33.33"),
			government_infra_pct=Decimal("33.33"),
			isea_pct=Decimal("0.01"),
		)
		territory = SRLService.assign_compartment(self.user)
		pip_state = PIPState.from_recycle3(profile, territory=territory)
		self.assertEqual(pip_state.territory, territory)
		self.assertEqual(pip_state.industry_group_code, territory.index)
		self.assertIsNotNone(pip_state.time_slot)
		self.assertIn(pip_state.time_slot_time_frame, ["past", "present_past", "present_future", "future"])
