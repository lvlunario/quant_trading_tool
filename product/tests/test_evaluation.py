from dataclasses import replace
import unittest

from atlas.evaluation import FoldSpec, SampleWindow, plan_fold


class EvaluationSplitTests(unittest.TestCase):
    def setUp(self):
        self.samples = tuple(SampleWindow(i, i, i + 2) for i in range(12))
        self.spec = FoldSpec(0, 5, 9, 9)

    def test_exact_partition_purges_touching_labels_and_excludes_holdout(self):
        split = plan_fold(self.samples, self.spec)
        self.assertEqual(split.train_sessions, (0, 1, 2))
        self.assertEqual(split.validation_sessions, (5, 6))
        self.assertEqual(split.purged_sessions, (3, 4, 7, 8))
        self.assertEqual(split.excluded_sessions, (9, 10, 11))
        self.assertEqual(sorted(sum((split.train_sessions, split.validation_sessions,
                                    split.purged_sessions, split.excluded_sessions), ())),
                         list(range(12)))

    def test_safety_gap_applies_to_label_maturity_not_only_decision(self):
        split = plan_fold(self.samples, replace(self.spec, gap_sessions=1))
        self.assertEqual(split.train_sessions, (0, 1))
        self.assertEqual(split.purged_sessions, (2, 3, 4, 7, 8))

    def test_future_features_and_invalid_label_windows_rejected(self):
        for args in ((1, 2, 3), (1, 0, 1), (1, 0, 0), (True, 0, 3),
                     (1.0, 0, 3), (1, -1, 3)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                SampleWindow(*args)

    def test_invalid_folds_cannot_enter_holdout(self):
        for args in ((0, 5, 10, 9), (5, 5, 9, 9), (0, 9, 5, 10),
                     (0, 5, 9, 9, 5), (0, 5, 9, 9, -1), (False, 5, 9, 9)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                FoldSpec(*args)

    def test_unsorted_duplicate_and_untyped_inputs_rejected(self):
        for samples in (self.samples[::-1], self.samples + (self.samples[-1],),
                        list(self.samples), (object(),), ()):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                plan_fold(samples, self.spec)
        with self.assertRaises(ValueError):
            plan_fold(self.samples, object())

    def test_empty_training_or_validation_fails_closed(self):
        for samples in ((SampleWindow(0, 0, 5), SampleWindow(5, 5, 6)),
                        (SampleWindow(0, 0, 1), SampleWindow(8, 8, 9))):
            with self.subTest(samples=samples), self.assertRaisesRegex(
                    ValueError, 'insufficient_split_samples'):
                plan_fold(samples, self.spec)

    def test_expanding_folds_keep_final_holdout_excluded(self):
        samples = tuple(SampleWindow(i, i, i + 5) for i in range(200))
        for spec, expected_train, expected_validation in (
                (FoldSpec(0, 80, 120, 160, 1), tuple(range(74)), tuple(range(80, 115))),
                (FoldSpec(0, 120, 160, 160, 1), tuple(range(114)), tuple(range(120, 155)))):
            with self.subTest(spec=spec):
                split = plan_fold(samples, spec)
                self.assertEqual(split.train_sessions, expected_train)
                self.assertEqual(split.validation_sessions, expected_validation)
                self.assertTrue(set(range(160, 200)).issubset(split.excluded_sessions))
                self.assertTrue(all(samples[i].label_end_session < spec.validation_start - 1
                                    for i in split.train_sessions))


if __name__ == '__main__':
    unittest.main()
