from dataclasses import replace
from decimal import Decimal
import unittest

from atlas.metrics import MetricDefinition, MetricValue, require_compatible


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.definition = MetricDefinition('MET_REVENUE', '1.0.0',
            'Reported revenue, unadjusted', 'money', 'USD', 'quarter',
            'missing', 'reported@1.0.0')

    def test_finite_zero_and_negative_are_not_missing(self):
        for value in ('0', '-10', '12.34'):
            operand = MetricValue(self.definition, Decimal(value))
            require_compatible(operand, operand)

    def test_each_semantic_difference_blocks_comparison(self):
        left = MetricValue(self.definition, Decimal('10'))
        changes = dict(metric_id='MET_OTHER', definition_version='2.0.0',
            formula='Adjusted revenue', unit='money_per_share', period='ttm',
            null_policy='not_meaningful', transform_version='reported@2.0.0')
        for field, value in changes.items():
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'incompatible_metric_definitions'):
                require_compatible(left, MetricValue(replace(self.definition, **{field: value}), Decimal('10')))

    def test_missing_stays_missing_not_zero(self):
        absent = MetricValue(self.definition, None, 'missing_source')
        self.assertIsNone(absent.value)
        with self.assertRaisesRegex(ValueError, 'metric_unavailable'):
            require_compatible(absent, MetricValue(self.definition, Decimal('0')))

    def test_not_meaningful_is_explicit(self):
        definition = replace(self.definition, null_policy='not_meaningful')
        MetricValue(definition, None, 'not_meaningful')
        with self.assertRaises(ValueError):
            MetricValue(self.definition, None, 'not_meaningful')

    def test_bad_values_and_reason_combinations_rejected(self):
        for value, reason in ((1.0, None), (True, None), (Decimal('NaN'), None),
                              (Decimal('Infinity'), None), (None, None),
                              (None, 'unknown'), (Decimal('1'), 'missing_source')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MetricValue(self.definition, value, reason)

    def test_invalid_definition_fields_rejected(self):
        for field, value in (('metric_id', 'revenue'), ('definition_version', True),
                ('formula', ''), ('unit', 'percent'), ('currency', 'EUR'),
                ('period', 'monthly'), ('null_policy', 'zero'), ('transform_version', 'latest')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(self.definition, **{field: value})

    def test_dimensionless_currency_must_be_absent(self):
        replace(self.definition, unit='ratio', currency=None)
        with self.assertRaises(ValueError):
            replace(self.definition, unit='ratio')

    def test_invalid_operands_rejected(self):
        with self.assertRaises(ValueError):
            require_compatible(None, None)
        with self.assertRaises(ValueError):
            MetricValue(None, Decimal('1'))
