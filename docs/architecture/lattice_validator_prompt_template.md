# Lattice Validator Prompt Template

Use this prompt pattern to force feature generation to obey the 12-compartment lattice rules.

## Prompt Pattern
I am building `[Feature Name]` for Lattice Compartment `[Index]` (`[Category]`).
Reference the database-backed lattice registry and apply these constraints:
1. Enforce the compartment time frame: `[Past | Present/Past | Present/Future | Future]`.
2. Enforce category logic for `[Category]`.
3. Enforce the compartment capacity limit of `[4^index value]`.
4. If validation passes, save to the target model and include compartment metadata in the response.

Generate:
- a Django service class method,
- serializer-level error payloads,
- and tests for pass/fail cases.

## Existing Runtime Validator Hook
The project now includes a reusable service function in `seeds/services.py`:
- `validate_idea_submission(compartment_id, raw_content, metadata=None)`

Expected metadata tags:
- `historical` for Past compartments
- `forecast` for Future compartments

## Example Prompt
I am building an ingestion module for Lattice Compartment 10 (Geography).
Use the lattice registry capacity 1,048,576 and Present/Past time-frame constraints.
Implement a Django service using `validate_idea_submission` and return deterministic errors for missing tags or capacity overflow.
