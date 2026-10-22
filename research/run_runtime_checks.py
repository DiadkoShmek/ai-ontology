"""Reproduce the finite systems test report; runs child processes, no network."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sqlite3
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []

    def startTest(self, test):
        self.started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        failed = {x[0] for x in self.failures + self.errors}
        skipped = {x[0] for x in self.skipped}
        self.rows.append({"test":test.id(), "status":"failed" if test in failed else
                          "skipped" if test in skipped else "passed",
                          "wall_ms":round((time.perf_counter()-self.started)*1000,3)})
        super().stopTest(test)


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "examples"))
    result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=Result).run(suite)
    sources = sorted([*(ROOT/"examples").glob("*.py"),
                      *(ROOT/"examples").glob("*.json")]) + [Path(__file__)]
    report = {"schema":"ontology-runtime-checks/1", "observed_at":datetime.now(timezone.utc).isoformat(),
              "kind":"developer-run-systems-tests", "llm_trials":0,
              "python":platform.python_version(), "sqlite":sqlite3.sqlite_version,
              "tests_run":result.testsRun, "success":result.wasSuccessful(),
              "results":result.rows,
              "sources":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              "limits":["authored fixtures", "no independent reviewer", "no real LLM inference",
                        "no physical power-loss test", "no million-record benchmark",
                        "hashes do not authenticate authors or establish semantic support"]}
    output = ROOT / "research/runtime-results.json"
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"tests":result.testsRun,"success":result.wasSuccessful(),"output":str(output.relative_to(ROOT))}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
