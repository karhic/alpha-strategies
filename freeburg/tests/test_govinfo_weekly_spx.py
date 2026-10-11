import unittest
from freeburg.tools.govinfo_weekly_spx import parse_weekly_table

class GovinfoWeeklyTests(unittest.TestCase):
    def test_averages_preserve_semantics(self):
        rows=[["Common Stock Prices and Yields"]+[""]*9,
              [""]*10,[""]*10,
              [""]*6+["Standard & Poor's composite index"]+[""]*3,
              ["Week ended:"]+[""]*9,
              ["2011: Oct 8."]+[""]*5+["1137.53","", "2.42",""],
              ["15."]+[""]*5+["1205.18","", "2.27",""]]
        z=parse_weekly_table(rows,"2011-10","example")
        self.assertEqual([x["friday"] for x in z],["2011-10-07","2011-10-14"])
        self.assertEqual(z[0]["weekly_spx_average"],1137.53)
        self.assertIn("NOT_FRIDAY_CLOSE",z[0]["status"])
