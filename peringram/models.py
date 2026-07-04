from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RecycleThreeAllocation(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recycle_allocations")
	corporation_rd = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("33.33"))
	people_small_business_qcqa = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("33.33"))
	government_infrastructure_protection = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("33.33"))
	isea_gdp_optimization = models.DecimalField(
		max_digits=4,
		decimal_places=2,
		default=Decimal("0.01"),
		validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("0.01"))],
		help_text="Optional ISEA GDP optimization amount (0.00 or 0.01).",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]

	def recycle_total(self):
		return (
			self.corporation_rd
			+ self.people_small_business_qcqa
			+ self.government_infrastructure_protection
		)

	def total_with_isea(self):
		return self.recycle_total() + self.isea_gdp_optimization

	def clean(self):
		base_total = self.recycle_total()
		if base_total not in {Decimal("99.99"), Decimal("100.00")}:
			raise ValidationError("Recycle3 core percentages must total 99.99 or 100.00.")

		effective_total = self.total_with_isea()
		if effective_total not in {Decimal("99.99"), Decimal("100.00")}:
			raise ValidationError("Recycle3 total with ISEA must total 99.99 or 100.00.")

	def __str__(self):
		return f"Recycle3 for {self.user}"


class BaseTrueSquareRootMap(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pip_maps")
	territory_name = models.CharField(max_length=150)
	lattice_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["territory_name"]

	def __str__(self):
		return self.territory_name


class IndustryGroup(models.Model):
	SECTOR_PRIMARY = "A"
	SECTOR_SECONDARY = "B"
	SECTOR_TERTIARY = "C"
	SECTOR_QUATERNARY = "D"

	SECTOR_CHOICES = [
		(SECTOR_PRIMARY, "Primary"),
		(SECTOR_SECONDARY, "Secondary"),
		(SECTOR_TERTIARY, "Tertiary"),
		(SECTOR_QUATERNARY, "Quaternary"),
	]

	code = models.PositiveSmallIntegerField(
		unique=True,
		validators=[MinValueValidator(1), MaxValueValidator(16)],
		help_text="Industry group number 1-16.",
	)
	sector = models.CharField(max_length=1, choices=SECTOR_CHOICES)
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["code"]

	@staticmethod
	def sector_for_group_code(group_code):
		if 1 <= group_code <= 4:
			return IndustryGroup.SECTOR_PRIMARY
		if 5 <= group_code <= 8:
			return IndustryGroup.SECTOR_SECONDARY
		if 9 <= group_code <= 12:
			return IndustryGroup.SECTOR_TERTIARY
		return IndustryGroup.SECTOR_QUATERNARY

	def save(self, *args, **kwargs):
		self.sector = self.sector_for_group_code(self.code)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Group {self.code} ({self.get_sector_display()})"


class Industry(models.Model):
	group = models.ForeignKey(IndustryGroup, on_delete=models.CASCADE, related_name="industries")
	code = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["group__code", "code"]
		constraints = [
			models.UniqueConstraint(fields=["group", "code"], name="unique_industry_code_per_group"),
		]

	def __str__(self):
		return f"G{self.group.code:02d}-I{self.code:02d} {self.name}"


class SubIndustry(models.Model):
	industry = models.ForeignKey(Industry, on_delete=models.CASCADE, related_name="sub_industries")
	code = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["industry__group__code", "industry__code", "code"]
		constraints = [
			models.UniqueConstraint(fields=["industry", "code"], name="unique_sub_industry_code_per_industry"),
		]

	def __str__(self):
		return f"G{self.industry.group.code:02d}-I{self.industry.code:02d}-S{self.code} {self.name}"


class ConvectionCompartment(models.Model):
	compartment_index = models.PositiveSmallIntegerField(
		unique=True,
		validators=[MinValueValidator(1), MaxValueValidator(24)],
	)
	world_clock_hour = models.PositiveSmallIntegerField(
		unique=True,
		validators=[MinValueValidator(0), MaxValueValidator(23)],
	)
	label = models.CharField(max_length=120)
	lattice_coordinate = models.CharField(max_length=120, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["compartment_index"]

	def __str__(self):
		return f"Compartment {self.compartment_index} (hour {self.world_clock_hour:02d})"


class LatticeCompartment(models.Model):
	TIME_PAST = "past"
	TIME_PRESENT_PAST = "present_past"
	TIME_PRESENT_FUTURE = "present_future"
	TIME_FUTURE = "future"

	TIME_FRAME_CHOICES = [
		(TIME_PAST, "Past"),
		(TIME_PRESENT_PAST, "Present/Past"),
		(TIME_PRESENT_FUTURE, "Present/Future"),
		(TIME_FUTURE, "Future"),
	]

	index = models.PositiveSmallIntegerField(
		unique=True,
		validators=[MinValueValidator(1), MaxValueValidator(12)],
		help_text="Lattice compartment number 1-12.",
	)
	color = models.CharField(max_length=20)
	time_frame = models.CharField(max_length=20, choices=TIME_FRAME_CHOICES)
	capacity = models.BigIntegerField(help_text="Geometric series capacity based on 4^index.")
	category = models.CharField(max_length=80)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["index"]

	def clean(self):
		super().clean()
		expected_capacity = 4 ** self.index
		if self.capacity != expected_capacity:
			raise ValidationError(
				{"capacity": f"Capacity for index {self.index} must equal {expected_capacity} (4^index)."}
			)

	def __str__(self):
		return f"L{self.index:02d} {self.category} ({self.get_time_frame_display()})"
