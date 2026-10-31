import unittest

from dealengine.anomaly import (
    MIN_OBS,
    classify,
    compute_baseline,
    confidence,
    detect_anomaly,
)


class TestBaseline(unittest.TestCase):
    def test_median_and_lowest_normal(self):
        hist = [500, 510, 490, 480, 520, 495, 505]
        m, ln = compute_baseline(hist)
        self.assertAlmostEqual(m, 500)
        self.assertAlmostEqual(ln, 480)


class TestDetect(unittest.TestCase):
    def setUp(self):
        # 30 days of stable ~480-520 USD observations
        self.hist = [480 + (i % 5) * 10 for i in range(30)]

    def test_no_anomaly_near_median(self):
        reasons, extreme = detect_anomaly(490, self.hist)
        self.assertIsNone(reasons)
        self.assertFalse(extreme)

    def test_insufficient_baseline(self):
        reasons, extreme = detect_anomaly(100, self.hist[:4])
        self.assertIsNone(reasons)
        self.assertEqual(MIN_OBS, 5)

    def test_flash_flagged(self):
        reasons, extreme = detect_anomaly(250, self.hist)
        self.assertIsNotNone(reasons)
        assert reasons is not None
        self.assertFalse(extreme)
        self.assertTrue(any("median" in r for r in reasons))
        self.assertEqual(classify(250, self.hist), "flash")

    def test_mistake_flagged(self):
        reasons, extreme = detect_anomaly(150, self.hist)
        self.assertIsNotNone(reasons)
        assert reasons is not None
        self.assertEqual(classify(150, self.hist), "mistake")

    def test_extreme_outlier_error_pattern(self):
        reasons, extreme = detect_anomaly(4.0, self.hist)
        assert reasons is not None
        self.assertTrue(extreme)
        self.assertTrue(any("extreme outlier" in r for r in reasons))

    def test_currency_mismatch_recorded(self):
        reasons, extreme = detect_anomaly(250, self.hist, currency="EUR", currency_modal="USD")
        assert reasons is not None
        self.assertTrue(any("currency mismatch" in r for r in reasons))


class TestConfidence(unittest.TestCase):
    def test_bootstrap_cap(self):
        # 3 days observed: base 1, +1 reverified = 2
        self.assertEqual(confidence(3, "flash", reverified=True), 2)

    def test_mature(self):
        # 120 days: base 4, +1 reverified = 5
        self.assertEqual(confidence(120, "flash", reverified=True), 5)

    def test_mistake_cap(self):
        # 120 days reverified would be 5, but mistake fares cap at 3
        self.assertEqual(confidence(120, "mistake", reverified=True), 3)

    def test_bounds(self):
        self.assertEqual(confidence(120, "verified", reverified=False), 4)
        self.assertEqual(confidence(2, "verified", reverified=False), 1)


if __name__ == "__main__":
    unittest.main()
