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
