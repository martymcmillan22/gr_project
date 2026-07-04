"""
BaseTrue Pattern Engine (BTPE) — Rule Library v1.0

Complete rule set for MLAS → BTPE → SVEM pattern generation.
Defines universal logic, color-driven patterns, industry behavior, and hard constraints.
"""

# ⭐ 1. GLOBAL PATTERN RULES (Always Apply)
GLOBAL_RULES = {
    'controlling_idea': 'Every story must express a single controlling idea — all sections must reinforce one thematic spine.',
    'mlas_mapping': 'Every pattern must map to MLAS → Dewey → Industry — classification determines structure.',
    'complexity_escalation': 'Every tier must escalate complexity — Tier 1 = simple, Tier 2 = structured, Tier 3 = multi-layered.',
    'determinism': 'Every output must be deterministic — same input → same output.',
    'reversibility': 'Every pattern must be reversible — BTPE must be able to invert a pattern.',
    'explainability': 'Every pattern must be explainable — BTPE must produce a rationale.',
    'composability': 'Every pattern must be composable — patterns can stack without conflict.',
    'industry_safety': 'Every pattern must be industry-safe — no illegal or non-compliant outputs.',
}

# ⭐ 2. MLAS → PATTERN RULES (Color-Driven)
MLAS_PATTERN_RULES = {
    'RED': {
        'name': 'Detection Patterns',
        'behaviors': [
            'Identify anomalies',
            'Surface contradictions',
            'Highlight missing metadata',
            'Generate "What\'s wrong?" patterns',
        ],
        'default_output_type': 'detection',
        'complexity': 1,
    },
    'BLUE': {
        'name': 'Communication Patterns',
        'behaviors': [
            'Clarify intent',
            'Generate messaging frameworks',
            'Produce narrative bridges',
        ],
        'default_output_type': 'narrative',
        'complexity': 2,
    },
    'YELLOW': {
        'name': 'Distribution Patterns',
        'behaviors': [
            'Break content into sequences',
            'Generate pipelines',
            'Create multi-step flows',
        ],
        'default_output_type': 'pipeline',
        'complexity': 2,
    },
    'GREEN': {
        'name': 'Repair Patterns',
        'behaviors': [
            'Resolve contradictions',
            'Suggest fixes',
            'Generate "patch" structures',
        ],
        'default_output_type': 'repair',
        'complexity': 2,
    },
    'PURPLE': {
        'name': 'Branching Patterns',
        'behaviors': [
            'Create forks',
            'Generate alternate timelines',
            'Build "what-if" structures',
        ],
        'default_output_type': 'branching',
        'complexity': 3,
    },
    'TEAL': {
        'name': 'Replication Patterns',
        'behaviors': [
            'Duplicate structures',
            'Create templates',
            'Generate reusable frameworks',
        ],
        'default_output_type': 'template',
        'complexity': 2,
    },
    'ORANGE': {
        'name': 'Formation Patterns',
        'behaviors': [
            'Build new structures',
            'Generate scaffolds',
            'Produce outlines',
        ],
        'default_output_type': 'scaffold',
        'complexity': 1,
    },
    'LIME': {
        'name': 'Publication Patterns',
        'behaviors': [
            'Format content',
            'Generate TOCs',
            'Produce final-form outputs',
        ],
        'default_output_type': 'publication',
        'complexity': 2,
    },
    'PINK': {
        'name': 'Structure Patterns',
        'behaviors': [
            'Enforce hierarchy',
            'Generate nested structures',
            'Produce multi-layer outlines',
        ],
        'default_output_type': 'hierarchy',
        'complexity': 3,
    },
    'CYAN': {
        'name': 'Function Patterns',
        'behaviors': [
            'Map roles',
            'Generate responsibilities',
            'Produce functional diagrams',
        ],
        'default_output_type': 'functional',
        'complexity': 2,
    },
    'AMBER': {
        'name': 'Genetics Patterns',
        'behaviors': [
            'Map lineage',
            'Generate inheritance structures',
            'Produce "origin → evolution" arcs',
        ],
        'default_output_type': 'genealogy',
        'complexity': 2,
    },
    'GREEN_LIME': {
        'name': 'Evolution Patterns',
        'behaviors': [
            'Predict future states',
            'Generate timelines',
            'Produce "next step" structures',
        ],
        'default_output_type': 'evolution',
        'complexity': 3,
    },
}

# ⭐ 3. INDUSTRY PATTERN RULES (Per-Industry Behavior)
INDUSTRY_RULES = {
    'FINANCIALS': {
        'name': 'Financials',
        'pattern_constraints': [
            'Patterns must be analytical',
            'Must include risk → mitigation → outcome',
            'Must include numeric anchors',
        ],
        'required_components': ['risk_analysis', 'mitigation_strategy', 'numeric_metrics'],
    },
    'COMMUNICATIONS': {
        'name': 'Communications',
        'pattern_constraints': [
            'Patterns must be narrative',
            'Must include audience → message → medium',
            'Must include tone mapping',
        ],
        'required_components': ['audience', 'message', 'medium', 'tone'],
    },
    'CONSUMER': {
        'name': 'Consumer',
        'pattern_constraints': [
            'Patterns must be experiential',
            'Must include user → action → reward',
            'Must include emotional beats',
        ],
        'required_components': ['user_persona', 'action_sequence', 'reward', 'emotional_beats'],
    },
    'INDUSTRIALS': {
        'name': 'Industrials',
        'pattern_constraints': [
            'Patterns must be operational',
            'Must include process → constraint → output',
            'Must include efficiency mapping',
        ],
        'required_components': ['process', 'constraints', 'output', 'efficiency_metrics'],
    },
}

# ⭐ 4. HARD CONSTRAINTS (Non-Negotiable)
HARD_CONSTRAINTS = [
    'No pattern may contradict MLAS classification',
    'No pattern may exceed tier complexity limits',
    'No pattern may generate illegal or non-compliant content',
    'No pattern may produce ambiguous hierarchy',
    'No pattern may produce circular logic',
    'No pattern may produce unbounded recursion',
    'No pattern may violate industry signatures',
    'No pattern may generate more than 3 layers without Tier 3 access',
]

# ⭐ 5. WORKED EXAMPLES (10–30 Examples)
WORKED_EXAMPLES = [
    {
        'id': 'ex_001',
        'title': 'MLAS: BLUE → Communications → Narrative Pattern',
        'input': 'Customer onboarding message',
        'mlas_color': 'BLUE',
        'mlas_category': 'Communications',
        'pattern_type': 'narrative',
        'output_structure': {
            'audience': 'new user',
            'message': 'welcome + next step',
            'medium': 'email',
            'tone': 'supportive',
            'structure': '3-step sequence',
        },
    },
    {
        'id': 'ex_002',
        'title': 'MLAS: RED → Industrials → Detection Pattern',
        'input': 'Manufacturing workflow',
        'mlas_color': 'RED',
        'mlas_category': 'Industrials',
        'pattern_type': 'detection',
        'output_structure': {
            'step_1': 'Detect bottleneck',
            'step_2': 'Identify constraint',
            'step_3': 'Highlight anomaly',
            'step_4': 'Suggest repair',
        },
    },
    {
        'id': 'ex_003',
        'title': 'MLAS: PURPLE → Consumer → Branching Pattern',
        'input': 'Mobile app user journey',
        'mlas_color': 'PURPLE',
        'mlas_category': 'Consumer',
        'pattern_type': 'branching',
        'output_structure': {
            'path_a': {'name': 'success', 'emotional_beats': ['discovery', 'delight', 'habit']},
            'path_b': {'name': 'friction', 'emotional_beats': ['confusion', 'frustration', 'retry']},
            'path_c': {'name': 'abandonment', 'emotional_beats': ['doubt', 'abandonment', 'loss']},
        },
    },
    {
        'id': 'ex_004',
        'title': 'MLAS: AMBER → Genetics Pattern',
        'input': 'Brand evolution',
        'mlas_color': 'AMBER',
        'mlas_category': 'Communications',
        'pattern_type': 'genealogy',
        'output_structure': {
            'origin_story': 'Founding narrative',
            'growth_phase': 'Expansion period',
            'mutation_event': 'Pivot or crisis',
            'current_form': 'Present identity',
            'future_evolution': 'Next chapter',
        },
    },
    {
        'id': 'ex_005',
        'title': 'MLAS: GREEN → Repair Pattern',
        'input': 'Broken narrative arc',
        'mlas_color': 'GREEN',
        'mlas_category': 'Communications',
        'pattern_type': 'repair',
        'output_structure': {
            'contradiction': 'Identified conflict',
            'fix_suggestion': 'Proposed resolution',
            'rebuilt_arc': 'New narrative flow',
            'coherence_check': 'Validation passed',
        },
    },
    {
        'id': 'ex_006',
        'title': 'MLAS: LIME → Publication Pattern',
        'input': 'Final report',
        'mlas_color': 'LIME',
        'mlas_category': 'Communications',
        'pattern_type': 'publication',
        'output_structure': {
            'format_toc': 'Table of contents',
            'generate_sections': 'Section breakdown',
            'produce_layout': 'Final formatting',
        },
    },
    {
        'id': 'ex_007',
        'title': 'MLAS: ORANGE → Formation Pattern',
        'input': 'New product concept',
        'mlas_color': 'ORANGE',
        'mlas_category': 'Consumer',
        'pattern_type': 'scaffold',
        'output_structure': {
            'core_idea': 'Central concept',
            'scaffold': 'Structural framework',
            'outline': 'Detailed breakdown',
            'pitch_structure': 'Presentation framework',
        },
    },
    {
        'id': 'ex_008',
        'title': 'MLAS: CYAN → Function Pattern',
        'input': 'Team roles',
        'mlas_color': 'CYAN',
        'mlas_category': 'Industrials',
        'pattern_type': 'functional',
        'output_structure': {
            'responsibilities': 'Role definitions',
            'interfaces': 'Interaction points',
            'functional_diagram': 'Role visualization',
        },
    },
    {
        'id': 'ex_009',
        'title': 'MLAS: GREEN_LIME → Evolution Pattern',
        'input': 'Roadmap',
        'mlas_color': 'GREEN_LIME',
        'mlas_category': 'Industrials',
        'pattern_type': 'evolution',
        'output_structure': {
            'current_state': 'Present situation',
            'next_step': 'Immediate action',
            'future_state': 'Medium term',
            'long_term_vision': 'Strategic goal',
        },
    },
    {
        'id': 'ex_010',
        'title': 'MLAS: TEAL → Replication Pattern',
        'input': 'Template request',
        'mlas_color': 'TEAL',
        'mlas_category': 'Communications',
        'pattern_type': 'template',
        'output_structure': {
            'structure': 'Duplicated framework',
            'parameterize': 'Variable fields',
            'template': 'Reusable format',
        },
    },
]

# Complexity tier limits
TIER_COMPLEXITY_LIMITS = {
    1: 1,      # Tier 1: max complexity 1 (simple patterns only)
    2: 2,      # Tier 2: max complexity 2 (structured patterns)
    3: 3,      # Tier 3: max complexity 3 (multi-layered patterns)
}
