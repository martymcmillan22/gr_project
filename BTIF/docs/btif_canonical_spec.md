# BTIF Canonical Specification

## Purpose
This document is the canonical source for the Base True Information Format (BTIF) core vocabulary and deterministic rules used by the Django data model and seed command.

## Core Hierarchy
- Subjects: 4
- Branches: 16 (4 per subject)
- Industries: 64 (4 per branch)
- Sub-industries: 256 (4 per industry)

## Subject Layer
1. Math
2. Language
3. Arts
4. Science

## Branch Compartments
- Math: SACP (Statistics, Algebra, Calculus, Probability)
- Language: EDNP (Expository, Descriptive, Narrative, Persuasive)
- Arts: VLSM (Visual, Literature, Sculpture, Music)
- Science: MBSP (Math Logic, Biology, Social, Physical)

## Temporal Slots (Tenses of Time)
- Past: 1 red, 5 purple, 9 pink
- Present-Past: 2 blue, 6 teal, 10 cyan
- Present-Future: 3 yellow, 7 orange, 11 amber
- Future: 4 green, 8 lime, 12 green-lime

## Phase Cycle
CPW order:
1. Create
2. Post
3. Work

## Seed Contract
The management command `seed_btif` must produce this minimum deterministic baseline:
- 4 subjects
- 16 branches
- 64 industries
- 256 sub-industries
- 12 temporal slots