from django.db import models


class NAICSReference(models.Model):
	code = models.CharField(max_length=12, unique=True, db_index=True)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, default="")
	sector_code = models.CharField(max_length=12, blank=True, default="")
	source_version = models.CharField(max_length=32, blank=True, default="")
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "platform_core_naicsreference"
		ordering = ["code"]

	def __str__(self):
		return f"NAICS {self.code} {self.title}".strip()


class GICSReference(models.Model):
	LEVEL_SECTOR = "sector"
	LEVEL_INDUSTRY_GROUP = "industry_group"
	LEVEL_INDUSTRY = "industry"
	LEVEL_SUB_INDUSTRY = "sub_industry"
	LEVEL_CHOICES = [
		(LEVEL_SECTOR, "Sector"),
		(LEVEL_INDUSTRY_GROUP, "Industry Group"),
		(LEVEL_INDUSTRY, "Industry"),
		(LEVEL_SUB_INDUSTRY, "Sub-Industry"),
	]

	code = models.CharField(max_length=24, db_index=True)
	name = models.CharField(max_length=255)
	level = models.CharField(max_length=24, choices=LEVEL_CHOICES, default=LEVEL_SUB_INDUSTRY, db_index=True)
	parent_code = models.CharField(max_length=24, blank=True, default="")
	description = models.TextField(blank=True, default="")
	source_version = models.CharField(max_length=32, blank=True, default="")
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "platform_core_gicsreference"
		ordering = ["level", "code"]

	def __str__(self):
		return f"GICS {self.level} {self.code} {self.name}".strip()


class PlatformReferenceNAICSReferenceSchema(models.Model):
	code = models.CharField(max_length=12, unique=True, db_index=True)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, default="")
	sector_code = models.CharField(max_length=12, blank=True, default="")
	source_version = models.CharField(max_length=32, blank=True, default="")
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = True
		db_table = "platform_reference_naicsreference"
		ordering = ["code"]
		indexes = [
			models.Index(fields=["sector_code", "code"], name="platform_re_sector__naics_idx"),
			models.Index(fields=["is_active", "code"], name="pr_naics_active_code_idx"),
		]

	def __str__(self):
		return f"NAICS {self.code} {self.title}".strip()


class PlatformReferenceGICSReferenceSchema(models.Model):
	LEVEL_SECTOR = "sector"
	LEVEL_INDUSTRY_GROUP = "industry_group"
	LEVEL_INDUSTRY = "industry"
	LEVEL_SUB_INDUSTRY = "sub_industry"
	LEVEL_CHOICES = [
		(LEVEL_SECTOR, "Sector"),
		(LEVEL_INDUSTRY_GROUP, "Industry Group"),
		(LEVEL_INDUSTRY, "Industry"),
		(LEVEL_SUB_INDUSTRY, "Sub-Industry"),
	]

	code = models.CharField(max_length=24, db_index=True)
	name = models.CharField(max_length=255)
	level = models.CharField(max_length=24, choices=LEVEL_CHOICES, default=LEVEL_SUB_INDUSTRY, db_index=True)
	parent_code = models.CharField(max_length=24, blank=True, default="")
	description = models.TextField(blank=True, default="")
	source_version = models.CharField(max_length=32, blank=True, default="")
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = True
		db_table = "platform_reference_gicsreference"
		ordering = ["level", "code"]
		constraints = [
			models.UniqueConstraint(fields=["code", "level"], name="platform_re_gics_code_level_unique"),
		]
		indexes = [
			models.Index(fields=["level", "code"], name="platform_re_level_gics_idx"),
			models.Index(fields=["parent_code", "level"], name="pr_gics_parent_level_idx"),
			models.Index(fields=["is_active", "level", "code"], name="platform_re_is_active_gics_idx"),
		]

	def __str__(self):
		return f"GICS {self.level} {self.code} {self.name}".strip()
