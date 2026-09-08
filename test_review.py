import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml
from review import UniqueLoader, review

ROOT = Path(__file__).parent

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.load((ROOT / "example.yml").read_text(), Loader=UniqueLoader)

    def test_expiration_enabled_and_disabled_are_distinct(self):
        result = review(self.config)["findings"]
        self.assertIn("7 days", result[0]["detail"])
        self.assertIn("disabled", result[1]["detail"])

    def test_missing_settings_stay_unknown(self):
        result = review({"GriefPrevention": {}})
        self.assertEqual({f["status"] for f in result["findings"]}, {"unknown"})

    def test_boolean_is_not_an_expiration_integer(self):
        self.config["GriefPrevention"]["Claims"]["Expiration"]["ChestClaimDays"] = True
        with self.assertRaises(ValueError): review(self.config)

    def test_negative_days_rejected(self):
        self.config["GriefPrevention"]["Claims"]["Expiration"]["ChestClaimDays"] = -1
        with self.assertRaises(ValueError): review(self.config)

    def test_quoted_boolean_rejected(self):
        self.config["GriefPrevention"]["PvP"]["ProtectPlayersInLandClaims"]["PlayerOwnedClaims"] = "false"
        with self.assertRaises(ValueError): review(self.config)

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError): yaml.load("a: 1\na: 2", Loader=UniqueLoader)

    def test_unsafe_tags_rejected(self):
        with self.assertRaises(yaml.YAMLError): yaml.load("!!python/object:builtins.object {}", Loader=UniqueLoader)

    def test_modes_and_immutability(self):
        before = copy.deepcopy(self.config)
        findings = review(self.config)["findings"]
        self.assertIn("do not protect", next(f for f in findings if f["setting"].endswith("nations"))["detail"])
        self.assertEqual(before, self.config)

    def test_unknown_mode_rejected(self):
        self.config["GriefPrevention"]["Claims"]["Mode"]["world"] = "typo"
        with self.assertRaises(ValueError): review(self.config)

    def test_cli_leaves_input_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yml"
            original = (ROOT / "example.yml").read_bytes()
            path.write_bytes(original)
            run = subprocess.run([sys.executable, str(ROOT / "review.py"), str(path)], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_cli_has_no_success_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yml"
            path.write_text("[]")
            run = subprocess.run([sys.executable, str(ROOT / "review.py"), str(path)], capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, b"")

if __name__ == "__main__": unittest.main()
