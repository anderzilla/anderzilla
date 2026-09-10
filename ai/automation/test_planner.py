import unittest
from planner import plan

class PlannerTests(unittest.TestCase):
    def test_no_dispatch(self):
        self.assertFalse(plan('media-cuts', media_id='owned_1')['dispatch'])

    def test_report_dates_required(self):
        for workflow in ['report-weekly', 'report-monthly', 'report-custom']:
            with self.subTest(workflow=workflow), self.assertRaises(ValueError):
                plan(workflow)

    def test_invalid_dates(self):
        for start, end in [('2026-09-10', '2026-09-01'), ('2026-02-30', '2026-03-01')]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                plan('report-custom', start=start, end=end)

    def test_period(self):
        self.assertEqual(plan('report-custom', start='2026-09-01', end='2026-10-01')['end_exclusive'], '2026-10-01')

    def test_unknown(self):
        with self.assertRaises(ValueError):
            plan('shell')

    def test_budget(self):
        for amount in ['-1', '11', 'NaN', 'Infinity']:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                plan('media-cuts', media_id='owned_1', estimated_brl=amount)

    def test_media_id(self):
        for media in [None, '../secret', 'https://example.org/video']:
            with self.subTest(media=media), self.assertRaises(ValueError):
                plan('media-cuts', media_id=media)
