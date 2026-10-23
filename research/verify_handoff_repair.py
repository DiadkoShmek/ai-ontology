"""Read-only verification of the saved prospective transport repair cohort."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent/"handoff_repair"
sys.path.insert(0, str(HERE))
from analyze import derive


def main():
    result = derive()
    if result != json.loads((HERE/"results.json").read_text()):
        raise ValueError("saved-repair-results-drift")
    print(json.dumps({"internally_consistent":True, "calls":result["captured_calls"],
                      "episodes":result["episodes"], "scope":result["scope"]}))


if __name__ == "__main__":
    main()
