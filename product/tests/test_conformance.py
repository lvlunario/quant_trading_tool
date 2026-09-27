"""M1 conformance statement must stay explicit, bounded and public-safe."""
import unittest

from atlas.conformance import m1_import_conformance


class ConformanceTests(unittest.TestCase):
    def test_status_counts_and_check_ids_are_consistent(self):
        report = m1_import_conformance()
        checks = report['checks']
        ids = [check['check_id'] for check in checks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(report['counts'], {
            'verified_synthetic': 4,
            'blocked_external_evidence': 4,
            'not_implemented': 1,
        })
        self.assertEqual(sum(report['counts'].values()), len(checks))
        self.assertEqual(report['overall_status'], 'partial_synthetic_only')

    def test_fidelity_checks_are_blocked_without_claiming_compatibility(self):
        report = m1_import_conformance()
        fidelity = [check for check in report['checks']
                    if check['check_id'].startswith('FID_')]
        self.assertTrue(fidelity)
        self.assertTrue(all(check['status'] == 'blocked_external_evidence'
                            for check in fidelity))
        rendered = str(report).lower()
        self.assertIn('no fidelity-specific parser', rendered)
        self.assertNotIn('fidelity-compatible', rendered)
        for private_marker in ('account number', 'holding quantity', 'customer name'):
            self.assertNotIn(private_marker, rendered)
