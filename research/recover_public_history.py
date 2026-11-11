"""Import the pinned, pseudonymized source archives needed for offline verification."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def recover():
    history = json.loads((ROOT / "research/public-history.json").read_text())
    with TemporaryDirectory() as temp:
        for name, archive in history["archives"].items():
            raw = subprocess.check_output(
                ["git", "show", f"{history['archive_commit']}:research/{name}"], cwd=ROOT
            )
            if sha256(raw).hexdigest() != archive["sha256"]:
                raise ValueError(f"public history archive hash mismatch: {name}")
            bundle = Path(temp) / name
            bundle.write_bytes(raw)
            subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=ROOT,
                           check=True, capture_output=True)
            subprocess.run(["git", "fetch", "--quiet", "--no-tags", str(bundle), archive["ref"]],
                           cwd=ROOT, check=True, capture_output=True)


if __name__ == "__main__":
    recover()
