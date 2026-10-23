"""Adversarial editorial changes; no model or network calls."""
import unittest
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import check_claim_history as checker
from check_claim_history import validate

REF = "a" * 40 + ":report.md"


def document(status="proposed", events=None):
    if events is None:
        events = [("1.0.0", "proposed", "Initial proposal.", REF)]
    return (
        "| ID | Status | Claim | Evidence and reproduction | Status and boundary |\n"
        "|---|---|---|---|---|\n"
        f"| C01 | `{status}` | A testable proposal. | See report. | Limited case. |\n\n"
        "| ID | Edition | Status | Reason | Evidence |\n"
        "|---|---|---|---|---|\n"
        + "".join(f"| C01 | {v} | `{s}` | {r} | `{e}` |\n" for v, s, r, e in events)
    )


class ClaimHistoryTests(unittest.TestCase):
    def check(self, current, edition="1.1.0", resolve=lambda commit, path: path == "report.md"):
        return validate(current, edition, document(), "1.0.0", resolve)

    def test_explicit_withdrawal_preserves_previous_assessment(self):
        current = document("withdrawn", [
            ("1.0.0", "proposed", "Initial proposal.", REF),
            ("1.1.0", "withdrawn", "Counterexample recorded.", REF),
        ])
        result = self.check(current)
        self.assertEqual(result["entries"], 2)
        self.assertFalse(result["semantic_support_verified"])

    def test_changed_status_without_entry_is_refused(self):
        with self.assertRaisesRegex(ValueError, "current status"):
            self.check(document("withdrawn"))

    def test_new_entry_without_new_edition_is_refused(self):
        current = document("withdrawn", [
            ("1.0.0", "proposed", "Initial proposal.", REF),
            ("1.1.0", "withdrawn", "Changed.", REF),
        ])
        # The 1.1.0 edition already exists without changing this claim. A
        # late edit may not borrow that existing edition for a status change.
        with self.assertRaisesRegex(ValueError, "new publication edition"):
            validate(current, "1.1.0", document(), "1.1.0", lambda commit, path: True)

    def test_missing_evidence_is_refused(self):
        current = document("withdrawn", [
            ("1.0.0", "proposed", "Initial proposal.", REF),
            ("1.1.0", "withdrawn", "Counterexample.", "b" * 40 + ":missing.md"),
        ])
        with self.assertRaisesRegex(ValueError, "evidence absent"):
            self.check(current)

    def test_rewritten_previous_reason_is_refused(self):
        current = document(events=[("1.0.0", "proposed", "A better-looking past.", REF)])
        with self.assertRaisesRegex(ValueError, "history prefix"):
            self.check(current)

    def test_deleted_history_is_refused(self):
        current = document("withdrawn", [("1.1.0", "withdrawn", "Only the new record.", REF)])
        with self.assertRaisesRegex(ValueError, "history prefix"):
            self.check(current)

    def test_mutable_reference_is_refused(self):
        current = document("withdrawn", [
            ("1.0.0", "proposed", "Initial proposal.", REF),
            ("1.1.0", "withdrawn", "Changed.", "HEAD:report.md"),
        ])
        with self.assertRaisesRegex(ValueError, "full commit"):
            self.check(current)

    def test_existing_source_does_not_prove_semantic_support(self):
        current = document("observed", [
            ("1.0.0", "proposed", "Initial proposal.", REF),
            ("1.1.0", "observed", "Unsubstantiated boast with a valid path.", REF),
        ])
        # Deliberate negative control: the editor, not this checker, must catch
        # a source whose contents do not support its attached assertion.
        self.assertFalse(self.check(current)["semantic_support_verified"])

    def test_metadata_only_rollback_uses_current_commit_as_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)

            def git(*args):
                subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "user.name=Fixture",
                                "-c", "user.email=fixture@example.invalid", "-C", folder, *args],
                               check=True, capture_output=True)

            git("init", "-q", "--template=")
            (root / "CLAIMS.md").write_text(document())
            (root / "edition.json").write_text(json.dumps({"version": "1.0.0"}))
            git("add", ".")
            git("commit", "-qm", "First edition")
            (root / "edition.json").write_text(json.dumps({"version": "2.0.0"}))
            git("add", ".")
            git("commit", "-qm", "New edition with unchanged claims")
            (root / "edition.json").write_text(json.dumps({"version": "1.0.0"}))
            with patch.object(checker, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "edition regressed"):
                    checker.main()


if __name__ == "__main__":
    unittest.main()
