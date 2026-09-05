import tempfile
import unittest
from pathlib import Path

from agent_quality_lab.experiments import SCENARIOS, run_trial, scripted_model
from agent_quality_lab.models import ScriptedModel
from agent_quality_lab.runtime import Completion


class ExperimentTests(unittest.TestCase):
    def test_each_scripted_scenario_has_state_and_trace_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            for scenario in SCENARIOS:
                with self.subTest(scenario=scenario):
                    path, report = run_trial(scripted_model(scenario), scenario, Path(directory),
                                             model_mode="scripted", model_name="scripted-test-double")
                    self.assertTrue(report["state_checks_passed"], report["checks"])
                    self.assertTrue(path.is_file())
                    self.assertTrue(report["events"])
                    self.assertTrue(report["manual_answer_review_required"])
                    self.assertIn("domain.py", report["source_sha256"])
                    self.assertEqual(report["model_mode"], "scripted")

    def test_false_success_answer_cannot_pass_state_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report = run_trial(ScriptedModel([Completion("已退款且工单处理完成")]), "normal", Path(directory),
                                  model_mode="scripted", model_name="false-success-test-double")
            self.assertFalse(report["state_checks_passed"])
            self.assertFalse(report["checks"]["refund_state"])
            self.assertFalse(report["checks"]["ticket_state"])

    def test_model_outage_is_not_counted_as_successful_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report = run_trial(ScriptedModel([]), "denied", Path(directory),
                                  model_mode="scripted", model_name="outage-test-double")
            self.assertFalse(report["state_checks_passed"])
            self.assertFalse(report["checks"]["runtime_responded"])
