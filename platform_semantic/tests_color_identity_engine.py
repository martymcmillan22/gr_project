from django.test import SimpleTestCase

from platform_semantic.services.color_identity_engine import build_local_index
from platform_semantic.services.color_identity_engine import COMPARTMENT_ANCHOR_BANDS
from platform_semantic.services.color_identity_engine import color_code_from_identity_rgb
from platform_semantic.services.color_identity_engine import decode_color_code
from platform_semantic.services.color_identity_engine import display_rgb
from platform_semantic.services.color_identity_engine import encode_color_code
from platform_semantic.services.color_identity_engine import encode_identity_and_display
from platform_semantic.services.color_identity_engine import encode_ontology_path
from platform_semantic.services.color_identity_engine import identity_rgb_from_color_code
from platform_semantic.services.color_identity_engine import morton_deinterleave_18
from platform_semantic.services.color_identity_engine import morton_interleave_18
from platform_semantic.services.color_identity_engine import resolve_ontology_path_to_indices
from platform_semantic.services.color_identity_engine import split_local_index


class ColorIdentityEngineTests(SimpleTestCase):
    def test_color_code_round_trip(self):
        color_code = encode_color_code(compartment_id=7, local_index=123456)
        compartment_id, local_index = decode_color_code(color_code)
        self.assertEqual(compartment_id, 7)
        self.assertEqual(local_index, 123456)

    def test_identity_rgb_round_trip(self):
        color_code = encode_color_code(compartment_id=15, local_index=1048575)
        r, g, b = identity_rgb_from_color_code(color_code)
        reconstructed = color_code_from_identity_rgb(r, g, b)
        self.assertEqual(reconstructed, color_code)

    def test_morton_deinterleave_round_trip(self):
        samples = [0, 1, 2, 3, 7, 511, 131071, 262143]
        for sample in samples:
            r6, g6, b6 = morton_deinterleave_18(sample)
            self.assertGreaterEqual(r6, 0)
            self.assertLessEqual(r6, 63)
            self.assertGreaterEqual(g6, 0)
            self.assertLessEqual(g6, 63)
            self.assertGreaterEqual(b6, 0)
            self.assertLessEqual(b6, 63)
            round_trip = morton_interleave_18(r6, g6, b6)
            self.assertEqual(round_trip, sample)

    def test_display_rgb_stays_in_anchor_band(self):
        local_index = 0
        for compartment_id, band in COMPARTMENT_ANCHOR_BANDS.items():
            r, g, b = display_rgb(compartment_id, local_index)
            self.assertGreaterEqual(r, band.r0)
            self.assertLessEqual(r, band.r0 + 63)
            self.assertGreaterEqual(g, band.g0)
            self.assertLessEqual(g, band.g0 + 63)
            self.assertGreaterEqual(b, band.b0)
            self.assertLessEqual(b, band.b0 + 63)

    def test_math_reference_node(self):
        payload = encode_identity_and_display(compartment_id=0, local_index=0)
        self.assertEqual(payload["identity_rgb"], (0, 0, 0))
        self.assertEqual(payload["display_rgb"], (192, 0, 0))

    def test_local_index_pack_unpack_round_trip(self):
        local_index = build_local_index(industry_index=3, subindustry_index=2, node_index=65535)
        industry_index, subindustry_index, node_index = split_local_index(local_index)
        self.assertEqual(industry_index, 3)
        self.assertEqual(subindustry_index, 2)
        self.assertEqual(node_index, 65535)

    def test_resolve_ontology_path_to_indices(self):
        resolved = resolve_ontology_path_to_indices(
            sector="Primary",
            subject="Math",
            industry="Capital Markets",
            subindustry="Algorithmic Trading Systems & Quantitative Analysis",
        )
        self.assertEqual(resolved, (0, 0, 0))

    def test_encode_ontology_path(self):
        payload = encode_ontology_path(
            sector="Primary",
            subject="Math",
            industry="Capital Markets",
            subindustry="Algorithmic Trading Systems & Quantitative Analysis",
            node_index=9,
        )
        self.assertEqual(payload["compartment_id"], 0)
        self.assertEqual(payload["local_index_fields"]["industry_index"], 0)
        self.assertEqual(payload["local_index_fields"]["subindustry_index"], 0)
        self.assertEqual(payload["local_index_fields"]["node_index"], 9)
        self.assertEqual(payload["identity_rgb"], (0, 0, 9))

    def test_resolve_phase4_ontology_path_to_indices(self):
        resolved = resolve_ontology_path_to_indices(
            sector="Quaternary",
            subject="Economics",
            industry="Banking",
            subindustry="Central Bank Reserve Interventions & Fractional Lending Math",
        )
        self.assertEqual(resolved, (14, 0, 0))

    def test_encode_phase4_ontology_path(self):
        payload = encode_ontology_path(
            sector="Quaternary",
            subject="Economics",
            industry="Banking",
            subindustry="Central Bank Reserve Interventions & Fractional Lending Math",
            node_index=21,
        )
        self.assertEqual(payload["compartment_id"], 14)
        self.assertEqual(payload["local_index_fields"]["industry_index"], 0)
        self.assertEqual(payload["local_index_fields"]["subindustry_index"], 0)
        self.assertEqual(payload["local_index_fields"]["node_index"], 21)
        self.assertEqual(payload["identity_rgb"], (224, 0, 21))
