from django.core.management.base import BaseCommand, CommandError

from ontology.services.linear_generator import generate_linear_hierarchy


class Command(BaseCommand):
	help = "Generate 4/16/64/256 hierarchy from a linear ordered set of 4 subjects."

	def add_arguments(self, parser):
		parser.add_argument(
			"--subjects",
			required=True,
			help="Comma-separated ordered subjects (exactly 4). Example: Math,Language,Arts,Science",
		)
		parser.add_argument(
			"--reset",
			action="store_true",
			help="Delete existing hierarchy before generating.",
		)

	def handle(self, *args, **options):
		subjects = [item.strip() for item in options["subjects"].split(",")]
		try:
			result = generate_linear_hierarchy(subjects, reset=options["reset"])
		except ValueError as exc:
			raise CommandError(str(exc)) from exc

		self.stdout.write(self.style.SUCCESS("Linear hierarchy generation complete."))
		self.stdout.write(
			f"Subjects: {result['subjects']}, Branches: {result['branches']}, "
			f"Industries: {result['industries']}, Sub-industries: {result['sub_industries']}"
		)
		self.stdout.write(f"Ordered subjects: {', '.join(result['subject_names'])}")