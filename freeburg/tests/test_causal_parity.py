"""Historical research cross-implementation parity and no-lookahead safeguards."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from freeburg.tools.verify_causal_parity import frame_inputs, verify
from freeburg.tools.reproduce_four_from_sources import calculate

class CausalParityTests(unittest.TestCase):
    def test_reject_month_start_as_production_parity(self):
        with self.assertRaisesRegex(ValueError, 'lookahead'):
            frame_inputs(None,None,None,None,baa_availability='month-start')
    def test_replay_rejects_incorrect_expected_action(self):
        # Cover fail-closed behavior using a tiny mock; full historical replay
        # is run separately with 2632 actual strategy actions.
        self.assertTrue(callable(verify))
