"""M1 conformance statement must stay explicit, bounded and public-safe."""
from copy import deepcopy
import unittest

from atlas.conformance import (m1_import_conformance, m1_milestone_handoff,
                               recommend_m1_disposition)


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

    def test_disposition_accepts_only_synthetic_evidence_and_defers_fidelity(self):
        disposition = recommend_m1_disposition()
        self.assertEqual(disposition['synthetic_scope'],
                         'recommend_accept_engineering_evidence')
        self.assertEqual(disposition['fidelity_scope'],
                         'recommend_defer_external_validation')
        self.assertEqual(disposition['phase_progression'],
                         'continue_synthetic_fallback')
        self.assertFalse(disposition['founder_approval_recorded'])
        self.assertFalse(disposition['release_authorized'])

    def test_disposition_rejects_tampered_evidence(self):
        report = deepcopy(m1_import_conformance())
        report['counts']['verified_synthetic'] += 1
        with self.assertRaises(ValueError):
            recommend_m1_disposition(report)

    def test_handoff_advances_only_synthetic_scope_to_m2(self):
        handoff = m1_milestone_handoff()
        self.assertEqual(handoff['engineering_state'],
                         'synthetic_scope_accepted_for_progression')
        self.assertEqual(handoff['fidelity_state'],
                         'deferred_pending_private_evidence')
        self.assertEqual((handoff['next_phase'], handoff['next_deadline']),
                         ('M2 Sourced Research', '2026-10-17'))
        self.assertFalse(handoff['founder_approval_recorded'])
        self.assertFalse(handoff['release_authorized'])
        self.assertIn('no holdings', handoff['data_notice'])

    def test_handoff_rejects_tampered_source_report(self):
        report = deepcopy(m1_import_conformance())
        report['overall_status'] = 'complete'
        with self.assertRaises(ValueError):
            m1_milestone_handoff(report)
        report = deepcopy(m1_import_conformance())
        report['checks'][4]['status'] = 'verified_synthetic'
        report['counts'] = {'verified_synthetic': 5,
                            'blocked_external_evidence': 3,
                            'not_implemented': 1}
        with self.assertRaises(ValueError):
            recommend_m1_disposition(report)
