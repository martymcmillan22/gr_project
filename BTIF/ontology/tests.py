from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ontology.models import Branch, Industry, Subject, SubIndustry, TemporalSlot
from ontology.services.lattice import build_lattice_nodes


class SeedBTIFCommandTests(TestCase):
	def test_seed_btif_creates_expected_counts(self):
		call_command("seed_btif")

		self.assertEqual(Subject.objects.count(), 4)
		self.assertEqual(Branch.objects.count(), 16)
		self.assertEqual(Industry.objects.count(), 64)
		self.assertEqual(SubIndustry.objects.count(), 256)
		self.assertEqual(TemporalSlot.objects.count(), 12)

	def test_temporal_slot_one_is_past_red(self):
		call_command("seed_btif")

		slot = TemporalSlot.objects.get(position=1)
		self.assertEqual(slot.tense, "past")
		self.assertEqual(slot.color, "red")


class LinearHierarchyGenerationTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_command_generates_4_16_64_256(self):
		call_command(
			"generate_linear_hierarchy",
			"--subjects",
			"Recycle,Maps,Sectors,Convection",
			"--reset",
		)

		self.assertEqual(Subject.objects.count(), 4)
		self.assertEqual(Branch.objects.count(), 16)
		self.assertEqual(Industry.objects.count(), 64)
		self.assertEqual(SubIndustry.objects.count(), 256)

	def test_generate_api_requires_auth(self):
		response = self.client.post(
			"/api/generate-linear-hierarchy/",
			{"subjects": ["A", "B", "C", "D"], "reset": True},
			format="json",
		)
		self.assertEqual(response.status_code, 401)

	def test_generate_api_builds_full_hierarchy(self):
		user = get_user_model().objects.create_user(
			username="linear_builder",
			email="builder@example.com",
			password="StrongBuildPass123",
		)
		token = Token.objects.create(user=user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		response = self.client.post(
			"/api/generate-linear-hierarchy/",
			{
				"subjects": ["Work", "Post", "Create", "Review"],
				"reset": True,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["subjects"], 4)
		self.assertEqual(response.data["branches"], 16)
		self.assertEqual(response.data["industries"], 64)
		self.assertEqual(response.data["sub_industries"], 256)

	def test_generate_api_returns_compartment_derivation_chain_and_colors(self):
		user = get_user_model().objects.create_user(
			username="compartment_builder",
			email="compartment@example.com",
			password="StrongBuildPass123",
		)
		token = Token.objects.create(user=user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		response = self.client.post(
			"/api/generate-linear-hierarchy/",
			{
				"subjects": ["Work", "Post", "Create", "Review"],
				"reset": True,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		compartments = response.data["compartments"]
		self.assertEqual(len(compartments), 12)

		expected_colors = [
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

		for idx, compartment in enumerate(compartments, start=1):
			self.assertEqual(compartment["position"], idx)
			self.assertEqual(compartment["color"], expected_colors[idx - 1])
			expected_parent = None if idx == 1 else idx - 1
			self.assertEqual(compartment["derived_from"], expected_parent)
			self.assertEqual(compartment["potential_files"], 4**idx)


class LatticeServiceTests(TestCase):
	def setUp(self):
		call_command("seed_btif", "--reset")

	def test_build_lattice_nodes_uses_temporal_cycle(self):
		nodes = build_lattice_nodes()

		self.assertEqual(len(nodes), 256)
		self.assertEqual(nodes[0]["position"], 1)
		self.assertEqual(nodes[0]["tense"], "past")
		self.assertEqual(nodes[0]["color"], "red")
		self.assertEqual(nodes[12]["position"], 1)


class MetaTermCommandTests(TestCase):
	def setUp(self):
		call_command("seed_btif", "--reset")

	def test_materialize_metaterms_replaces_placeholder_names(self):
		target = SubIndustry.objects.order_by("id").first()
		self.assertIn(" Sub ", target.name)

		call_command("materialize_metaterms")
		target.refresh_from_db()

		self.assertTrue(target.name.endswith("Foundations"))

	def test_materialize_metaterms_dry_run_makes_no_changes(self):
		target = SubIndustry.objects.order_by("id").first()
		original = target.name

		call_command("materialize_metaterms", "--dry-run")
		target.refresh_from_db()

		self.assertEqual(target.name, original)


class OntologyApiTests(TestCase):
	def setUp(self):
		call_command("seed_btif", "--reset")
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="btif_writer",
			email="writer@example.com",
			password="StrongTestPass123",
		)

	def test_subjects_endpoint_returns_seeded_data(self):
		response = self.client.get("/api/subjects/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 4)

	def test_health_endpoint_returns_version_and_status(self):
		response = self.client.get("/health/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["project"], "BTIF")
		self.assertEqual(response.json()["status"], "ok")
		self.assertIn("version", response.json())

	def test_lattice_map_endpoint_returns_full_map(self):
		response = self.client.get("/api/lattice-map/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 256)
		self.assertEqual(len(response.data["results"]), 256)

	def test_branches_filter_by_subject_name(self):
		response = self.client.get("/api/branches/?subject=Math")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 4)
		self.assertTrue(all(item["subject_name"] == "Math" for item in response.data["results"]))

	def test_temporal_slots_filter_by_tense(self):
		response = self.client.get("/api/temporal-slots/?tense=past")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 3)

	def test_lattice_map_filter_by_tense(self):
		response = self.client.get("/api/lattice-map/?tense=past")

		self.assertEqual(response.status_code, 200)
		self.assertGreater(response.data["count"], 0)
		self.assertTrue(all(row["tense"] == "past" for row in response.data["results"]))

	def test_lattice_export_csv(self):
		response = self.client.get("/api/lattice-map/export/?export=csv")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response["Content-Type"], "text/csv")
		body = response.content.decode("utf-8")
		self.assertIn("subject,branch,industry", body)

	def test_write_requires_authentication(self):
		subject = Subject.objects.get(name="Math")
		response = self.client.patch(
			f"/api/subjects/{subject.id}/",
			{"description": "updated without auth"},
			format="json",
		)

		self.assertEqual(response.status_code, 401)

	def test_authenticated_write_succeeds(self):
		subject = Subject.objects.get(name="Math")
		self.client.force_authenticate(user=self.user)

		response = self.client.patch(
			f"/api/subjects/{subject.id}/",
			{"description": "updated with auth"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		subject.refresh_from_db()
		self.assertEqual(subject.description, "updated with auth")


class TokenAuthApiTests(TestCase):
	def setUp(self):
		call_command("seed_btif", "--reset")
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="token_user",
			email="token@example.com",
			password="StrongTokenPass123",
		)

	def test_obtain_token_success(self):
		response = self.client.post(
			"/api/auth/token/",
			{"username": "token_user", "password": "StrongTokenPass123"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("token", response.data)

	def test_register_success_returns_token_and_user(self):
		response = self.client.post(
			"/api/auth/register/",
			{
				"username": "new_user",
				"email": "new@example.com",
				"password": "StrongTokenPass123",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertIn("token", response.data)
		self.assertEqual(response.data["user"]["username"], "new_user")

	def test_register_duplicate_username_returns_400(self):
		response = self.client.post(
			"/api/auth/register/",
			{
				"username": "token_user",
				"email": "other@example.com",
				"password": "StrongTokenPass123",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 400)

	def test_token_auth_can_write(self):
		token = Token.objects.create(user=self.user)
		subject = Subject.objects.get(name="Math")
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		response = self.client.patch(
			f"/api/subjects/{subject.id}/",
			{"description": "token-updated"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		subject.refresh_from_db()
		self.assertEqual(subject.description, "token-updated")

	def test_auth_me_returns_current_user(self):
		token = Token.objects.create(user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		response = self.client.get("/api/auth/me/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["username"], "token_user")

	def test_revoke_token_invalidates_it(self):
		token = Token.objects.create(user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		revoke_response = self.client.post("/api/auth/token/revoke/")
		self.assertEqual(revoke_response.status_code, 200)
		self.assertFalse(Token.objects.filter(key=token.key).exists())
