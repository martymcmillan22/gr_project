from django.conf import settings
from django.db import models


class Idea(models.Model):
	STATUS_RAW = "RAW"
	STATUS_SEED = "SEED"
	STATUS_BUSINESS = "BUSINESS"
	STATUS_CHOICES = [
		(STATUS_RAW, "Raw"),
		(STATUS_SEED, "Seed"),
		(STATUS_BUSINESS, "Business"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="ideas",
	)
	industry = models.ForeignKey(
		"peringram.Industry",
		on_delete=models.PROTECT,
		related_name="ideas",
	)
	raw_content = models.TextField()
	status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RAW)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]

	def __str__(self):
		return f"Idea {self.id} ({self.status})"


class Seed(models.Model):
	idea = models.OneToOneField(Idea, on_delete=models.CASCADE, related_name="seed")
	polish_notes = models.JSONField(default=dict, blank=True)
	germination_date = models.DateField(auto_now_add=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-germination_date", "-updated_at"]

	def __str__(self):
		return f"Seed for Idea {self.idea_id}"


class Business(models.Model):
	seed = models.OneToOneField(Seed, on_delete=models.CASCADE, related_name="business")
	brand_name = models.CharField(max_length=160)
	market_status = models.CharField(max_length=80)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]

	def __str__(self):
		return self.brand_name


class CrossReference(models.Model):
	RELATION_SIMILAR = "similar"
	RELATION_SUPPLIES = "supplies"
	RELATION_DEPENDS_ON = "depends_on"
	RELATION_COMPLEMENTS = "complements"
	RELATION_CHOICES = [
		(RELATION_SIMILAR, "Similar"),
		(RELATION_SUPPLIES, "Supplies"),
		(RELATION_DEPENDS_ON, "Depends On"),
		(RELATION_COMPLEMENTS, "Complements"),
	]

	source_business = models.ForeignKey(
		Business,
		on_delete=models.CASCADE,
		related_name="outgoing_cross_references",
	)
	target_business = models.ForeignKey(
		Business,
		on_delete=models.CASCADE,
		related_name="incoming_cross_references",
	)
	relationship_type = models.CharField(max_length=32, choices=RELATION_CHOICES)
	score = models.DecimalField(max_digits=6, decimal_places=5, default=0.00000)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-score", "-created_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["source_business", "target_business", "relationship_type"],
				name="ux_cr_source_target_type",
			),
			models.CheckConstraint(
				condition=~models.Q(source_business=models.F("target_business")),
				name="ck_cr_no_self_reference",
			),
		]

	def __str__(self):
		return (
			f"{self.source_business_id} -> {self.target_business_id} "
			f"({self.relationship_type}, {self.score})"
		)
