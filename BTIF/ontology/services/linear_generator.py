from django.db import transaction

from ontology.models import Branch, Industry, Subject, SubIndustry


SUBJECT_TENSE_SEQUENCE = ["past", "present_past", "present_future", "future"]
INVERSE_ORDER_MAP = {1: 4, 2: 3, 3: 2, 4: 1}

# Example macro-perspective progression from the chat.
BRANCH_WORDS = ["Collection", "Description", "Analysis", "Conclusion"]
INDUSTRY_WORDS = ["Past", "Present-Past", "Present-Future", "Future"]
META_WORDS = ["Core", "Applied", "Automation", "Quality"]
COMPARTMENT_COLORS = [
	"red",
	"blue",
	"yellow",
	"green",
	"purple",
	"teal",
	"orange",
	"lime",
	"pink",
	"cyan",
	"amber",
	"green-lime",
]


def _clean_subjects(subject_names):
	cleaned = [name.strip() for name in subject_names if str(name).strip()]
	if len(cleaned) != 4:
		raise ValueError("Exactly 4 non-empty subjects are required.")
	if len(set(name.lower() for name in cleaned)) != 4:
		raise ValueError("Subjects must be unique.")
	return cleaned


def _truncate(text, max_length):
	return text[:max_length]


def _acronym_from_words(words):
	letters = []
	for word in words[:4]:
		parts = [p for p in str(word).replace("-", " ").split() if p]
		if not parts:
			continue
		letters.append(parts[0][0].upper())
	if not letters:
		return "COMP"
	return "".join(letters)[:8]


def _subject_acronym(name, order, used, subject_names):
	# Subject compartment acronym is derived from the first letters of the 4 ordered subjects.
	base = _acronym_from_words(subject_names)
	if not base:
		base = "SUBJ"

	acronym = base
	if acronym in used:
		fallback = _acronym_from_words([name]) or "SUB"
		acronym = f"{fallback[:3]}{order}"[:8]

	while acronym in used:
		acronym = f"{base[:3]}{order}"[:8]

	used.add(acronym)
	return acronym


def _build_subject_description(subject_name, order, tense):
	inverse_order = INVERSE_ORDER_MAP[order]
	return (
		"Auto-generated from linear format order. "
		f"Macro perspective tense: {tense}. "
		f"Inverse pair order: {order}<->{inverse_order}."
	)


def _build_compartment_chain():
	# Compartment 1 is the seed; each later compartment derives from the previous compartment.
	compartments = []
	for idx, color in enumerate(COMPARTMENT_COLORS, start=1):
		compartments.append(
			{
				"position": idx,
				"color": color,
				"derived_from": idx - 1 if idx > 1 else None,
				"potential_files": 4**idx,
			}
		)
	return compartments


def _build_potential_files_map(compartments):
	# 12 compartments: 4^1=4 through 4^12=16,777,216.
	return {item["position"]: item["potential_files"] for item in compartments}


def _branch_compartment_acronym():
	# Branch acronym from the first letter of each of the 4 words.
	return _acronym_from_words(BRANCH_WORDS)


def _subject_compartment_acronym(subject_names):
	# Compartment acronym from the first letter of the 4 ordered subjects.
	return _acronym_from_words(subject_names)


def _industry_name(subject, branch, industry_word):
	return f"{subject.name} {branch.name} {industry_word}"


def _sub_industry_name(industry, meta_word):
	return f"{industry.name} {meta_word}"


def _build_subject_tense_map(subject_names):
	result = []
	for idx, name in enumerate(subject_names, start=1):
		result.append(
			{
				"order": idx,
				"subject": name,
				"tense": SUBJECT_TENSE_SEQUENCE[idx - 1],
				"inverse_order": INVERSE_ORDER_MAP[idx],
			}
		)
	return result


def _branch_name_for_order(order):
	return BRANCH_WORDS[order - 1]


def _industry_word_for_order(order):
	return INDUSTRY_WORDS[order - 1]


def _meta_word_for_order(order):
	return META_WORDS[order - 1]


@transaction.atomic
def generate_linear_hierarchy(subject_names, reset=False):
	subject_names = _clean_subjects(subject_names)

	if reset:
		SubIndustry.objects.all().delete()
		Industry.objects.all().delete()
		Branch.objects.all().delete()
		Subject.objects.all().delete()
	elif Subject.objects.exists():
		raise ValueError("Hierarchy already exists. Pass reset=True to regenerate.")

	used_subject_acronyms = set()
	created_subjects = []
	branch_acronym = _branch_compartment_acronym()
	subject_compartment_acronym = _subject_compartment_acronym(subject_names)
	subject_tense_map = _build_subject_tense_map(subject_names)
	compartments = _build_compartment_chain()
	potential_files_by_compartment = _build_potential_files_map(compartments)

	for idx, subject_name in enumerate(subject_names, start=1):
		tense = SUBJECT_TENSE_SEQUENCE[idx - 1]
		subject = Subject.objects.create(
			name=_truncate(subject_name, 120),
			acronym=_subject_acronym(subject_name, idx, used_subject_acronyms, subject_names),
			order=idx,
			description=_truncate(_build_subject_description(subject_name, idx, tense), 1000),
		)
		created_subjects.append(subject)

		for branch_idx in range(1, 5):
			branch_name = _branch_name_for_order(branch_idx)
			branch = Branch.objects.create(
				subject=subject,
				name=_truncate(branch_name, 120),
				acronym=_truncate(branch_acronym, 8),
				order=branch_idx,
			)

			for industry_idx in range(1, 5):
				industry_word = _industry_word_for_order(industry_idx)
				industry = Industry.objects.create(
					branch=branch,
					name=_truncate(_industry_name(subject, branch, industry_word), 180),
					order=industry_idx,
				)

				for sub_idx in range(1, 5):
					meta_word = _meta_word_for_order(sub_idx)
					SubIndustry.objects.create(
						industry=industry,
						name=_truncate(_sub_industry_name(industry, meta_word), 220),
						order=sub_idx,
					)

	return {
		"subjects": Subject.objects.count(),
		"branches": Branch.objects.count(),
		"industries": Industry.objects.count(),
		"sub_industries": SubIndustry.objects.count(),
		"subject_names": [subject.name for subject in created_subjects],
		"subject_compartment_acronym": subject_compartment_acronym,
		"branch_compartment_acronym": branch_acronym,
		"subject_tense_map": subject_tense_map,
		"compartments": compartments,
		"potential_files_by_compartment": potential_files_by_compartment,
	}