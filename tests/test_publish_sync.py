import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("publisher", Path(__file__).resolve().parents[1] / "tools/publish-sync.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class ValidationGateTests(unittest.TestCase):
    def exercise(self, runs, jobs=None, timeout=20):
        responses = [SimpleNamespace(stdout=json.dumps(runs))]
        if jobs is not None:
            responses.append(SimpleNamespace(stdout=json.dumps({"jobs": jobs})))
        with patch.object(publisher, "run", side_effect=responses) as command:
            with patch.object(publisher.time, "monotonic", side_effect=[0, 0, 100]):
                with patch.object(publisher.time, "sleep"):
                    publisher.wait_for_validation("head", timeout=timeout)
        return command

    def run_record(self, status="completed", conclusion="success", sha="head", number=1):
        return dict(databaseId=number, status=status, conclusion=conclusion, headSha=sha)

    def test_success_requires_validate_job(self):
        self.exercise([self.run_record()], [{"name": "validate", "conclusion": "success"}])

    def test_failed_and_cancelled_runs_block(self):
        for result in ("failure", "cancelled", "skipped", "action_required"):
            with self.subTest(result=result), self.assertRaises(SystemExit):
                self.exercise([self.run_record(conclusion=result)])

    def test_approval_wait_blocks(self):
        with self.assertRaisesRegex(SystemExit, "approval"):
            self.exercise([self.run_record(status="waiting", conclusion="")])

    def test_missing_or_skipped_job_blocks(self):
        for jobs in ([], [{"name": "validate", "conclusion": "skipped"}]):
            with self.subTest(jobs=jobs), self.assertRaises(SystemExit):
                self.exercise([self.run_record()], jobs)

    def test_absent_and_wrong_commit_runs_timeout(self):
        for runs in ([], [self.run_record(sha="old")]):
            with self.subTest(runs=runs), self.assertRaisesRegex(SystemExit, "Timed out"):
                self.exercise(runs)

    def test_latest_attempt_must_pass(self):
        with self.assertRaises(SystemExit):
            self.exercise([self.run_record(), self.run_record(conclusion="failure", number=2)])


if __name__ == "__main__":
    unittest.main()
