from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from users.models import User

from .models import (
	ConvectionCompartment,
	Industry,
	IndustryGroup,
	LatticeCompartment,
	RecycleThreeAllocation,
	SubIndustry,
)


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
		allocation = RecycleThreeAllocation(
			user=self.user,
			corporation_rd=Decimal("33.33"),
			people_small_business_qcqa=Decimal("33.33"),
			government_infrastructure_protection=Decimal("33.33"),
			isea_gdp_optimization=Decimal("0.01"),
		)
		allocation.full_clean()
		self.assertEqual(allocation.recycle_total(), Decimal("99.99"))
		self.assertEqual(allocation.total_with_isea(), Decimal("100.00"))

	def test_domain_ordering_for_key_groups(self):
		self.client.force_login(self.user)
		self.client.get(reverse("peringram:dashboard"))
		self.assertEqual(IndustryGroup.objects.get(code=1).name, "Math")
		self.assertEqual(IndustryGroup.objects.get(code=2).name, "Language")
		self.assertEqual(IndustryGroup.objects.get(code=3).name, "Arts")
		self.assertEqual(IndustryGroup.objects.get(code=4).name, "Science")
		self.assertEqual(IndustryGroup.objects.get(code=10).name, "Geology")
