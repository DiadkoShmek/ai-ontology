"""The generic baseline may preserve all evidence; codec overflow must stay HOLD."""
import unittest
from study import derive


class FileControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = derive()

    def test_plain_files_are_information_equivalent_without_channel_cap(self):
        for row in self.result["cases"]:
            self.assertTrue(row["generic_history_exact"])
            if row["exact_admitted"]:
                self.assertTrue(row["decoded_bytes_equal"])
                self.assertTrue(row["receiver_prompt_equal"])

    def test_plain_files_exceed_this_small_transport_cap(self):
        for row in self.result["cases"]:
            self.assertFalse(row["generic_within_channel"])

    def test_variable_log_exposes_bounded_failure(self):
        rows = [row for row in self.result["cases"] if row["scenario"] == "variable-log"]
        self.assertEqual(len(rows), 8)
        for row in rows:
            self.assertFalse(row["exact_admitted"])
            self.assertEqual(row["hold_reason"], "complete-handoff-exceeds-capacity")
            self.assertIsNone(row["receiver_prompt_equal"])

    def test_no_model_score_is_invented(self):
        self.assertEqual(self.result["llm_calls"], 0)
        self.assertNotIn("model_success", self.result)


if __name__ == "__main__":
    unittest.main()
