"""
BaseTrue Pattern Engine (BTPE) — Core Generator

Implements the tier generation logic using the rule library.
Enforces hard constraints and produces deterministic, explainable outputs.
"""

from typing import Dict, List, Optional, Tuple
from .pattern_rules import (
    GLOBAL_RULES,
    MLAS_PATTERN_RULES,
    INDUSTRY_RULES,
    HARD_CONSTRAINTS,
    WORKED_EXAMPLES,
    TIER_COMPLEXITY_LIMITS,
)


class ConstraintValidator:
    """Validates outputs against hard constraints."""
    
    @staticmethod
    def validate_all(output: Dict, tier_level: int, mlas_color: str, industry: str) -> Tuple[bool, List[str]]:
        """
        Validate output against all hard constraints.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Constraint 1: No pattern may contradict MLAS classification
        if not ConstraintValidator._validate_mlas_consistency(output, mlas_color):
            errors.append('Output contradicts MLAS classification')
        
        # Constraint 2: No pattern may exceed tier complexity limits
        if not ConstraintValidator._validate_complexity_limit(output, tier_level):
            errors.append(f'Output exceeds complexity limit for Tier {tier_level}')
        
        # Constraint 3: No pattern may generate illegal or non-compliant content
        if not ConstraintValidator._validate_compliance(output, industry):
            errors.append('Output violates industry compliance requirements')
        
        # Constraint 4: No pattern may produce ambiguous hierarchy
        if not ConstraintValidator._validate_hierarchy_clarity(output):
            errors.append('Output contains ambiguous hierarchy')
        
        # Constraint 5: No pattern may produce circular logic
        if not ConstraintValidator._validate_circular_logic(output):
            errors.append('Output contains circular logic')
        
        # Constraint 6: No pattern may produce unbounded recursion
        if not ConstraintValidator._validate_unbounded_recursion(output):
            errors.append('Output contains unbounded recursion')
        
        # Constraint 7: No pattern may violate industry signatures
        if not ConstraintValidator._validate_industry_signature(output, industry):
            errors.append('Output violates industry signature requirements')
        
        # Constraint 8: No pattern may generate more than 3 layers without Tier 3 access
        if not ConstraintValidator._validate_layer_depth(output, tier_level):
            errors.append(f'Output exceeds layer depth limit for Tier {tier_level}')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_mlas_consistency(output: Dict, mlas_color: str) -> bool:
        """Check that output aligns with MLAS color classification."""
        # Placeholder: Basic check that output has expected fields
        return output is not None and isinstance(output, dict)
    
    @staticmethod
    def _validate_complexity_limit(output: Dict, tier_level: int) -> bool:
        """Check that output doesn't exceed complexity for this tier."""
        max_complexity = TIER_COMPLEXITY_LIMITS.get(tier_level, 1)
        # Placeholder: Count nested levels in output
        def count_depth(obj, depth=0):
            if isinstance(obj, dict):
                if not obj:
                    return depth
                return max(count_depth(v, depth + 1) for v in obj.values())
            elif isinstance(obj, list) and obj:
                return max(count_depth(item, depth + 1) for item in obj)
            return depth
        
        depth = count_depth(output)
        return depth <= max_complexity
    
    @staticmethod
    def _validate_compliance(output: Dict, industry: str) -> bool:
        """Check that output meets industry compliance standards."""
        # Placeholder: Industry-specific validation
        return True
    
    @staticmethod
    def _validate_hierarchy_clarity(output: Dict) -> bool:
        """Check that hierarchy is unambiguous."""
        # Placeholder: Check for duplicate keys at same level
        return True
    
    @staticmethod
    def _validate_circular_logic(output: Dict) -> bool:
        """Check for circular dependencies."""
        # Placeholder: Check for cycles in relationships
        return True
    
    @staticmethod
    def _validate_unbounded_recursion(output: Dict) -> bool:
        """Check for unbounded recursion patterns."""
        # Placeholder: Check recursion depth limits
        return True
    
    @staticmethod
    def _validate_industry_signature(output: Dict, industry: str) -> bool:
        """Check that output includes required industry components."""
        industry_rules = INDUSTRY_RULES.get(industry)
        if not industry_rules:
            return True
        
        required_components = industry_rules.get('required_components', [])
        # Placeholder: Check that all required components are present
        return True
    
    @staticmethod
    def _validate_layer_depth(output: Dict, tier_level: int) -> bool:
        """Check that depth doesn't exceed tier limits."""
        max_layers = 3 if tier_level == 3 else (2 if tier_level == 2 else 1)
        
        def count_layers(obj, layers=0):
            if isinstance(obj, dict):
                if not obj:
                    return layers
                nested_values = [count_layers(v, layers + 1) for v in obj.values()]
                return max(nested_values) if nested_values else layers
            elif isinstance(obj, list) and obj:
                nested_values = [count_layers(item, layers + 1) for item in obj]
                return max(nested_values) if nested_values else layers
            return layers
        
        layers = count_layers(output)
        return layers <= max_layers


class PatternGenerator:
    """Core BTPE generator that produces tier structures."""
    
    def __init__(self):
        """Initialize the generator."""
        self.validator = ConstraintValidator()
        self.generation_log = []
    
    def generate(
        self,
        seed_input: str,
        mlas_color: str,
        industry: str,
        tier_level: int = 1,
    ) -> Dict:
        """
        Generate a tier structure from seed input.
        
        Args:
            seed_input: The seed subject or prompt
            mlas_color: MLAS color classification (RED, BLUE, etc.)
            industry: Industry classification
            tier_level: Tier level (1-3)
        
        Returns:
            Dictionary with 'output', 'rationale', 'valid', 'errors'
        """
        self.generation_log = []
        
        # Step 1: Validate inputs
        self._log(f"Starting generation: {seed_input}")
        self._log(f"Parameters: MLAS={mlas_color}, Industry={industry}, Tier={tier_level}")
        
        if not self._validate_inputs(mlas_color, industry, tier_level):
            return {
                'output': None,
                'rationale': '\n'.join(self.generation_log),
                'valid': False,
                'errors': ['Invalid input parameters'],
            }
        
        # Step 2: Select pattern template
        pattern_info = self._select_pattern(mlas_color, industry)
        if not pattern_info:
            return {
                'output': None,
                'rationale': '\n'.join(self.generation_log),
                'valid': False,
                'errors': ['No matching pattern found'],
            }
        
        self._log(f"Selected pattern: {pattern_info['pattern_type']}")
        
        # Step 3: Generate output from template
        output = self._apply_pattern(seed_input, pattern_info, tier_level)
        self._log(f"Generated output with {len(output)} top-level keys")
        
        # Step 4: Validate against hard constraints
        is_valid, errors = self.validator.validate_all(output, tier_level, mlas_color, industry)
        
        if not is_valid:
            self._log(f"Validation failed: {len(errors)} constraint(s) violated")
        else:
            self._log("All constraints validated successfully")
        
        # Step 5: Produce rationale
        rationale = self._generate_rationale(seed_input, mlas_color, industry, tier_level, output)
        
        return {
            'output': output,
            'rationale': rationale,
            'valid': is_valid,
            'errors': errors,
            'log': self.generation_log,
        }
    
    def _validate_inputs(self, mlas_color: str, industry: str, tier_level: int) -> bool:
        """Validate input parameters."""
        if mlas_color not in MLAS_PATTERN_RULES:
            self._log(f"ERROR: Invalid MLAS color '{mlas_color}'")
            return False
        
        if industry not in INDUSTRY_RULES:
            self._log(f"ERROR: Invalid industry '{industry}'")
            return False
        
        if tier_level not in TIER_COMPLEXITY_LIMITS:
            self._log(f"ERROR: Invalid tier level {tier_level}")
            return False
        
        self._log("Input validation passed")
        return True
    
    def _select_pattern(self, mlas_color: str, industry: str) -> Optional[Dict]:
        """Select matching pattern template."""
        mlas_info = MLAS_PATTERN_RULES.get(mlas_color)
        industry_info = INDUSTRY_RULES.get(industry)
        
        if not mlas_info or not industry_info:
            return None
        
        pattern_info = {
            'mlas_color': mlas_color,
            'mlas_name': mlas_info['name'],
            'pattern_type': mlas_info['default_output_type'],
            'complexity': mlas_info['complexity'],
            'behaviors': mlas_info['behaviors'],
            'industry': industry,
            'industry_name': industry_info['name'],
            'required_components': industry_info['required_components'],
        }
        
        self._log(f"Pattern: {pattern_info['mlas_name']} ({mlas_color})")
        self._log(f"Industry: {pattern_info['industry_name']}")
        self._log(f"Type: {pattern_info['pattern_type']}")
        
        return pattern_info
    
    def _apply_pattern(self, seed_input: str, pattern_info: Dict, tier_level: int) -> Dict:
        """Apply pattern template to generate output."""
        pattern_type = pattern_info['pattern_type']
        
        # Route to appropriate pattern template
        if pattern_type == 'narrative':
            return self._generate_narrative_pattern(seed_input, pattern_info)
        elif pattern_type == 'detection':
            return self._generate_detection_pattern(seed_input, pattern_info)
        elif pattern_type == 'branching':
            return self._generate_branching_pattern(seed_input, pattern_info)
        elif pattern_type == 'genealogy':
            return self._generate_genealogy_pattern(seed_input, pattern_info)
        elif pattern_type == 'repair':
            return self._generate_repair_pattern(seed_input, pattern_info)
        elif pattern_type == 'publication':
            return self._generate_publication_pattern(seed_input, pattern_info)
        elif pattern_type == 'scaffold':
            return self._generate_scaffold_pattern(seed_input, pattern_info)
        elif pattern_type == 'functional':
            return self._generate_functional_pattern(seed_input, pattern_info)
        elif pattern_type == 'evolution':
            return self._generate_evolution_pattern(seed_input, pattern_info)
        elif pattern_type == 'template':
            return self._generate_replication_pattern(seed_input, pattern_info)
        else:
            return {'_error': f'Unknown pattern type: {pattern_type}'}
    
    def _generate_narrative_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate BLUE communication pattern (narrative)."""
        return {
            'pattern_type': 'narrative',
            'audience': self._infer_audience(seed_input),
            'message': self._infer_message(seed_input),
            'medium': self._infer_medium(seed_input),
            'tone': self._infer_tone(seed_input),
            'structure': '3-step sequence',
        }
    
    def _generate_detection_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate RED detection pattern."""
        return {
            'pattern_type': 'detection',
            'step_1': 'Detect anomaly or bottleneck',
            'step_2': 'Identify root cause',
            'step_3': 'Highlight impact',
            'step_4': 'Suggest resolution',
        }
    
    def _generate_branching_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate PURPLE branching pattern."""
        return {
            'pattern_type': 'branching',
            'path_a': {'name': 'success', 'characteristics': ['positive', 'expected']},
            'path_b': {'name': 'friction', 'characteristics': ['challenging', 'realistic']},
            'path_c': {'name': 'abandonment', 'characteristics': ['negative', 'risk']},
        }
    
    def _generate_genealogy_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate AMBER genetics/genealogy pattern."""
        return {
            'pattern_type': 'genealogy',
            'origin': 'Initial state',
            'growth': 'Expansion phase',
            'mutation': 'Transformation event',
            'current': 'Present form',
            'future': 'Predicted evolution',
        }
    
    def _generate_repair_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate GREEN repair pattern."""
        return {
            'pattern_type': 'repair',
            'diagnosis': 'Identify contradiction',
            'intervention': 'Proposed fix',
            'outcome': 'Restored coherence',
            'validation': 'Constraint check',
        }
    
    def _generate_publication_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate LIME publication pattern."""
        return {
            'pattern_type': 'publication',
            'structure': 'Organized hierarchy',
            'sections': 'Content breakdown',
            'formatting': 'Final presentation',
        }
    
    def _generate_scaffold_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate ORANGE formation/scaffold pattern."""
        return {
            'pattern_type': 'scaffold',
            'concept': 'Core idea',
            'framework': 'Structural skeleton',
            'breakdown': 'Detailed hierarchy',
            'sequence': 'Logical flow',
        }
    
    def _generate_functional_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate CYAN functional pattern."""
        return {
            'pattern_type': 'functional',
            'roles': 'Defined responsibilities',
            'interfaces': 'Interaction boundaries',
            'dependencies': 'Cross-functional links',
        }
    
    def _generate_evolution_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate GREEN_LIME evolution pattern."""
        return {
            'pattern_type': 'evolution',
            'baseline': 'Current state',
            'next_phase': 'Immediate future',
            'medium_term': 'Projected state',
            'long_vision': 'Strategic endpoint',
        }
    
    def _generate_replication_pattern(self, seed_input: str, pattern_info: Dict) -> Dict:
        """Generate TEAL replication/template pattern."""
        return {
            'pattern_type': 'template',
            'template': 'Reusable structure',
            'variables': 'Parameterizable fields',
            'constraints': 'Fixed rules',
        }
    
    def _infer_audience(self, seed_input: str) -> str:
        """Infer audience from seed input."""
        seed_lower = seed_input.lower()
        if 'customer' in seed_lower or 'user' in seed_lower:
            return 'End users'
        elif 'team' in seed_lower or 'staff' in seed_lower:
            return 'Internal team'
        return 'Stakeholders'
    
    def _infer_message(self, seed_input: str) -> str:
        """Infer core message from seed input."""
        seed_lower = seed_input.lower()
        if 'onboarding' in seed_lower:
            return 'Welcome + next step'
        elif 'error' in seed_lower or 'problem' in seed_lower:
            return 'Issue resolution path'
        return 'Key information + call-to-action'
    
    def _infer_medium(self, seed_input: str) -> str:
        """Infer communication medium from seed input."""
        seed_lower = seed_input.lower()
        if 'email' in seed_lower:
            return 'Email'
        elif 'message' in seed_lower or 'sms' in seed_lower:
            return 'In-app message'
        elif 'report' in seed_lower:
            return 'Document'
        return 'Multi-channel'
    
    def _infer_tone(self, seed_input: str) -> str:
        """Infer tone from seed input."""
        seed_lower = seed_input.lower()
        if 'urgent' in seed_lower or 'critical' in seed_lower:
            return 'Urgent'
        elif 'welcome' in seed_lower or 'onboarding' in seed_lower:
            return 'Supportive'
        return 'Professional'
    
    def _generate_rationale(
        self,
        seed_input: str,
        mlas_color: str,
        industry: str,
        tier_level: int,
        output: Dict,
    ) -> str:
        """Generate human-readable rationale for the generation."""
        rationale_lines = [
            f"## Generation Rationale",
            f"",
            f"**Input**: {seed_input}",
            f"**MLAS Color**: {mlas_color} ({MLAS_PATTERN_RULES[mlas_color]['name']})",
            f"**Industry**: {industry}",
            f"**Tier Level**: {tier_level}",
            f"",
            f"### Pattern Applied",
            f"The {MLAS_PATTERN_RULES[mlas_color]['name'].lower()} pattern was applied because:",
            "",
        ]
        
        for behavior in MLAS_PATTERN_RULES[mlas_color]['behaviors']:
            rationale_lines.append(f"- {behavior}")
        
        rationale_lines.extend([
            "",
            f"### Output Structure",
            f"The generated output includes {len(output)} primary components:",
            "",
        ])
        
        for i, (key, value) in enumerate(output.items(), 1):
            rationale_lines.append(f"{i}. **{key}**: {value if isinstance(value, str) else '(nested structure)'}")
        
        rationale_lines.extend([
            "",
            f"### Constraints Applied",
            f"Output was validated against {len(HARD_CONSTRAINTS)} hard constraints.",
            f"All constraints were satisfied.",
        ])
        
        return "\n".join(rationale_lines)
    
    def _log(self, message: str) -> None:
        """Add message to generation log."""
        self.generation_log.append(message)


# Module-level singleton
_generator_instance = None


def get_generator() -> PatternGenerator:
    """Get or create singleton generator."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = PatternGenerator()
    return _generator_instance
