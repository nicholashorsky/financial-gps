"""FIRE variant guidance coverage."""

import unittest

from shared.fire_variants import FIRE_VARIANT_GUIDANCE, FIRE_VARIANTS, fire_variant_label


class FireVariantGuidanceTests(unittest.TestCase):
    def test_all_supported_variants_have_neutral_guidance(self) -> None:
        self.assertEqual(FIRE_VARIANTS, ("lean", "coast", "barista", "fat"))
        for variant in FIRE_VARIANTS:
            with self.subTest(variant=variant):
                guidance = FIRE_VARIANT_GUIDANCE[variant]
                self.assertTrue(guidance["definition"])
                self.assertTrue(guidance["impact"])
                self.assertEqual(fire_variant_label(variant), guidance["label"])


if __name__ == "__main__":
    unittest.main()
