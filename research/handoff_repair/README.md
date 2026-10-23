# Exact journal handoff: experimental repair

This adapter preserves the whole reference journal across a bounded text
channel. It applies the method's requirement that exact evidence remain
accessible at the next decision. Encoding uses ordinary zlib and Base85.
It makes no claim of a new compression algorithm or a measured reading effect.

The public v3.2.0 study and its negative results remain unchanged. This directory
owns a separate prospective engineering check. It is not installed in a live
House service or automatically adopted by other agent sessions.

## Use without a model or network

From the repository root:

```sh
python3 -m unittest discover -s research/handoff_repair -v
```

With both `examples` and `research/handoff_repair` on your Python import path:

```python
import hashlib
from durable import Journal
from transport import export_journal, context_from_handoff

journal = Journal("your-owned-existing.sqlite")
wire, tail = export_journal(journal, branch="main", scope="your-release",
                            capacity=3136)
pin = hashlib.sha256(wire).hexdigest()
# Transfer wire and this exact descriptor through your chosen trusted storage.
# The 64-byte pin plus wire fit a 3200-byte transport budget if export succeeds.
context = context_from_handoff(
    wire, expected_sha256=pin, branch="main", scope="your-release",
    topic="your-topic", capacity=3136,
)
```

`export_journal` reads a consistent SQLite transaction. `context_from_handoff`
restores/replays the exact operations and uses the existing `durable.packet`
context builder. A separate Python process can restore stdin through
`transport.py --expected-sha256 PIN --branch main --scope SCOPE --capacity 3136`.

Whole-history overflow raises `Hold` before inference. There is no truncation,
hidden retrieval or provider fallback. Larger histories need an explicitly
different storage/retrieval contract; this codec is not a scalable memory system.
The decoder caps output at 256 KiB and enforces the runtime's operation bounds.

The pin checks consistency relative to a trusted external descriptor. Replacing
both descriptor and payload can forge a different valid snapshot. Hashes do not
authenticate an actor; compression does not encrypt private material. A captured
head is historical. New live decisions still need the current journal's CAS and
their own action authorization. No generated code is executed.

## Model experiment

[Protocol](PROTOCOL.md) defines the fixed sample, comparison, primary outcome,
resource accounting and limits. `run.py freeze` registers local inputs;
`run.py run` explicitly contacts the already authenticated model route. It
refuses changed/uncommitted inputs or existing output and never silently retries
failed outcomes. These commands are not part of offline verification.

After an actual run, `python3 -O research/handoff_repair/analyze.py` reconstructs
delivery, prompts, terminal metadata, scores and written proposed-plan files.
It makes no inference calls. Raw final replies and native completion/usage
events are retained. Reproduction is a new cohort and must use a fresh directory
or checkout; it must not replace this record.
