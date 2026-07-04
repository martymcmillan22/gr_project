from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


ORDER_VALIDATORS = [MinValueValidator(1), MaxValueValidator(4)]
POSITION_VALIDATORS = [MinValueValidator(1), MaxValueValidator(12)]


class CPWPhase(models.TextChoices):
	CREATE = "create", "Create"
	POST = "post", "Post"
	WORK = "work", "Work"


class Tense(models.TextChoices):
	PAST = "past", "Past"
	PRESENT_PAST = "present_past", "Present-Past"
	PRESENT_FUTURE = "present_future", "Present-Future"
	FUTURE = "future", "Future"


class Subject(models.Model):
	name = models.CharField(max_length=120, unique=True)
	acronym = models.CharField(max_length=8, unique=True)
	order = models.PositiveSmallIntegerField(validators=ORDER_VALIDATORS, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["order", "name"]

	def __str__(self):
		return f"{self.order}. {self.name}"


class Branch(models.Model):
	subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="branches")
	name = models.CharField(max_length=120)
	acronym = models.CharField(max_length=8)
	order = models.PositiveSmallIntegerField(validators=ORDER_VALIDATORS)

	class Meta:
		ordering = ["subject__order", "order", "name"]
		constraints = [
			models.UniqueConstraint(fields=["subject", "name"], name="uniq_branch_subject_name"),
			models.UniqueConstraint(fields=["subject", "order"], name="uniq_branch_subject_order"),
		]

	def __str__(self):
		return f"{self.subject.name} / {self.name}"


class Industry(models.Model):
	branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="industries")
	name = models.CharField(max_length=180)
	order = models.PositiveSmallIntegerField(validators=ORDER_VALIDATORS)

	class Meta:
		ordering = ["branch__subject__order", "branch__order", "order", "name"]
		constraints = [
			models.UniqueConstraint(fields=["branch", "name"], name="uniq_industry_branch_name"),
			models.UniqueConstraint(fields=["branch", "order"], name="uniq_industry_branch_order"),
		]

	def __str__(self):
		return f"{self.branch.name} / {self.name}"


class SubIndustry(models.Model):
	industry = models.ForeignKey(Industry, on_delete=models.CASCADE, related_name="sub_industries")
	name = models.CharField(max_length=220)
	order = models.PositiveSmallIntegerField(validators=ORDER_VALIDATORS)

	class Meta:
		ordering = [
			"industry__branch__subject__order",
			"industry__branch__order",
			"industry__order",
			"order",
			"name",
		]
		constraints = [
			models.UniqueConstraint(fields=["industry", "name"], name="uniq_subindustry_industry_name"),
			models.UniqueConstraint(fields=["industry", "order"], name="uniq_subindustry_industry_order"),
		]

	def __str__(self):
		return f"{self.industry.name} / {self.name}"


class TemporalSlot(models.Model):
	position = models.PositiveSmallIntegerField(unique=True, validators=POSITION_VALIDATORS)
	tense = models.CharField(max_length=32, choices=Tense.choices)
	color = models.CharField(max_length=32)
	default_phase = models.CharField(max_length=16, choices=CPWPhase.choices, default=CPWPhase.POST)

	class Meta:
		ordering = ["position"]

	def __str__(self):
		return f"{self.position}: {self.tense} / {self.color}"
