"""
BaseTrue Pattern Engine Models

Stores tier definitions, industry profiles, and generated pattern structures.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class IndustryProfile(models.Model):
    """Configuration profile for an industry category."""
    
    INDUSTRY_CHOICES = [
        ('FINANCIALS', 'Financials'),
        ('COMMUNICATIONS', 'Communications'),
        ('CONSUMER', 'Consumer'),
        ('INDUSTRIALS', 'Industrials'),
    ]
    
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    required_components = models.JSONField(default=list, help_text='Required fields for patterns in this industry')
    pattern_constraints = models.JSONField(default=list, help_text='Constraints specific to this industry')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.industry})"
    
    class Meta:
        verbose_name_plural = "Industry Profiles"
        ordering = ['industry']


class TierDefinition(models.Model):
    """Definition of a single tier in the hierarchical structure."""
    
    TIER_CHOICES = [(i, f'Tier {i}') for i in range(1, 4)]
    COLOR_CHOICES = [
        ('RED', 'Red - Detection'),
        ('BLUE', 'Blue - Communication'),
        ('YELLOW', 'Yellow - Distribution'),
        ('GREEN', 'Green - Repair'),
        ('PURPLE', 'Purple - Branching'),
        ('TEAL', 'Teal - Replication'),
        ('ORANGE', 'Orange - Formation'),
        ('LIME', 'Lime - Publication'),
        ('PINK', 'Pink - Structure'),
        ('CYAN', 'Cyan - Function'),
        ('AMBER', 'Amber - Genetics'),
        ('GREEN_LIME', 'Green-Lime - Evolution'),
    ]
    
    tier_level = models.IntegerField(choices=TIER_CHOICES, help_text='Complexity level: 1-3')
    mlas_color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    industry = models.ForeignKey(IndustryProfile, on_delete=models.CASCADE, related_name='tier_definitions')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    pattern_type = models.CharField(max_length=50, help_text='Pattern classification')
    complexity = models.IntegerField(help_text='Complexity rating 1-3')
    
    # Structure definition
    required_fields = models.JSONField(default=dict, help_text='Required output fields for this tier')
    behaviors = models.JSONField(default=list, help_text='Behaviors this tier should exhibit')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (Tier {self.tier_level}, {self.mlas_color})"
    
    class Meta:
        unique_together = ('tier_level', 'mlas_color', 'industry')
        ordering = ['tier_level', 'mlas_color']


class GeneratedTier(models.Model):
    """Output from the BTPE generator."""
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    seed_input = models.CharField(max_length=500, help_text='The seed subject or input prompt')
    tier_definition = models.ForeignKey(TierDefinition, on_delete=models.CASCADE, related_name='generated_tiers')
    
    # Generated content
    output = models.JSONField(help_text='Generated tier structure')
    rationale = models.TextField(blank=True, help_text='Explanation of how the output was generated')
    
    # Validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    constraints_validated = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_tiers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Generated Tier: {self.seed_input[:50]} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]


class SVEMTier(models.Model):
    """SVEM (4 branches per MLAS) tier in the hierarchy."""
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    parent_tier = models.ForeignKey(GeneratedTier, on_delete=models.CASCADE, related_name='svem_branches')
    branch_number = models.IntegerField(choices=[(i, f'Branch {i}') for i in range(1, 5)], help_text='Branch 1-4 under parent tier')
    
    # Inherited context
    seed_input = models.CharField(max_length=500, help_text='Seed from parent + branch specialization')
    mlas_color = models.CharField(max_length=20, help_text='Inherited MLAS color from parent')
    industry = models.CharField(max_length=50, help_text='Inherited industry from parent')
    
    # Generated content
    output = models.JSONField(help_text='Generated SVEM branch structure')
    rationale = models.TextField(blank=True, help_text='Explanation of branch generation')
    
    # Validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    constraints_validated = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"SVEM Branch {self.branch_number}: {self.seed_input[:40]}"
    
    class Meta:
        unique_together = ('parent_tier', 'branch_number')
        ordering = ['parent_tier', 'branch_number']
        indexes = [
            models.Index(fields=['parent_tier', 'branch_number']),
            models.Index(fields=['-created_at']),
        ]


class CCCPTier(models.Model):
    """CCCP (4 compartments per SVEM branch) tier in the hierarchy."""
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    parent_svem_tier = models.ForeignKey(SVEMTier, on_delete=models.CASCADE, related_name='cccp_compartments')
    compartment_number = models.IntegerField(choices=[(i, f'Compartment {i}') for i in range(1, 5)], help_text='Compartment 1-4 under parent SVEM branch')
    
    # Inherited context
    seed_input = models.CharField(max_length=500, help_text='Seed from parent SVEM + compartment specialization')
    mlas_color = models.CharField(max_length=20, help_text='Inherited MLAS color from root tier')
    industry = models.CharField(max_length=50, help_text='Inherited industry from root tier')
    
    # Generated content
    output = models.JSONField(help_text='Generated CCCP compartment structure')
    rationale = models.TextField(blank=True, help_text='Explanation of compartment generation')
    
    # Validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    constraints_validated = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        branch_num = self.parent_svem_tier.branch_number
        return f"CCCP Comp {self.compartment_number} (B{branch_num}): {self.seed_input[:30]}"
    
    class Meta:
        unique_together = ('parent_svem_tier', 'compartment_number')
        ordering = ['parent_svem_tier', 'compartment_number']
        indexes = [
            models.Index(fields=['parent_svem_tier', 'compartment_number']),
            models.Index(fields=['-created_at']),
        ]


class DCHDTier(models.Model):
    """DCHD (4 subcells per CCCP compartment) tier in the hierarchy."""
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    parent_cccp_tier = models.ForeignKey(CCCPTier, on_delete=models.CASCADE, related_name='dchd_subcells')
    subcell_number = models.IntegerField(choices=[(i, f'Subcell {i}') for i in range(1, 5)], help_text='Subcell 1-4 under parent CCCP compartment')
    
    # Inherited context
    seed_input = models.CharField(max_length=500, help_text='Seed from parent CCCP + subcell specialization')
    mlas_color = models.CharField(max_length=20, help_text='Inherited MLAS color from root tier')
    industry = models.CharField(max_length=50, help_text='Inherited industry from root tier')
    
    # Generated content
    output = models.JSONField(help_text='Generated DCHD subcell structure')
    rationale = models.TextField(blank=True, help_text='Explanation of subcell generation')
    
    # Validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    constraints_validated = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        cccp_num = self.parent_cccp_tier.compartment_number
        svem_num = self.parent_cccp_tier.parent_svem_tier.branch_number
        return f"DCHD Subcell {self.subcell_number} (C{cccp_num}B{svem_num}): {self.seed_input[:25]}"
    
    class Meta:
        unique_together = ('parent_cccp_tier', 'subcell_number')
        ordering = ['parent_cccp_tier', 'subcell_number']
        indexes = [
            models.Index(fields=['parent_cccp_tier', 'subcell_number']),
            models.Index(fields=['-created_at']),
        ]


class StoryScaffold(models.Model):
    """Persisted story scaffolding sections mapped to hierarchy nodes."""

    NODE_TYPE_CHOICES = [
        ('root', 'Root'),
        ('svem', 'SVEM'),
        ('cccp', 'CCCP'),
        ('dchd', 'DCHD'),
    ]

    DECISION_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    root_tier = models.ForeignKey(GeneratedTier, on_delete=models.CASCADE, related_name='story_scaffolds')
    node_key = models.CharField(max_length=80, help_text='Unique key within root hierarchy, e.g. svem:12')
    node_type = models.CharField(max_length=10, choices=NODE_TYPE_CHOICES)
    node_id = models.PositiveIntegerField(null=True, blank=True)

    timeline_lattice_index = models.IntegerField(null=True, blank=True)
    timeline_label = models.CharField(max_length=120, blank=True)
    semantic_intent_id = models.CharField(max_length=120, blank=True)

    talking_points = models.TextField(blank=True)
    core_concept = models.TextField(blank=True)
    synopsis = models.TextField(blank=True)
    chapter_structure = models.TextField(blank=True)
    dchd_atoms = models.JSONField(default=list, blank=True)
    scaffold_version = models.PositiveIntegerField(default=1)

    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='draft')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_story_scaffolds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Scaffold {self.node_key} on root {self.root_tier_id}"

    class Meta:
        unique_together = ('root_tier', 'node_key')
        ordering = ['root_tier', 'node_key']
        indexes = [
            models.Index(fields=['root_tier', 'node_key']),
            models.Index(fields=['root_tier', '-updated_at']),
        ]


class PatternTemplate(models.Model):
    """Reusable pattern template."""
    
    name = models.CharField(max_length=200, unique=True)
    mlas_color = models.CharField(max_length=20)
    pattern_type = models.CharField(max_length=50)
    template_structure = models.JSONField(help_text='Reusable template structure')
    description = models.TextField(blank=True)
    example_input = models.CharField(max_length=500, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.mlas_color})"
    
    class Meta:
        ordering = ['mlas_color', 'name']
