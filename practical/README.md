# Continue a real repository check after a process reset

```sh
python3 practical/publication_handoff.py
```

Python 3.11+, no installation, network or model. Run from a clone with the
research archives present. The command creates and removes only its own
temporary directory. An explicit `--output NEW_FILE.json` preserves a report
using exclusive creation; it never replaces an existing file.

## The task

This example runs four fixed offline gates against the actual repository:
transport tests, generic-file controls, measurement-integrity tests and the
saved repair-cohort verifier. It records actual exits/stdout/stderr, plus exact
source/data hashes, in the reference SQLite journal.

It then exports that evidence and restores it in a **fresh Python process**.
The consumer checks the captured evidence against the currently readable
checkout. It does not execute commands found in the journal. Finally, a copy of
the permitted source is changed inside the owned temporary directory; another
fresh consumer rejects the old evidence and identifies the changed file.
The user's checkout is never changed.

[The retained run](publication-handoff-results.json) checked 79 files, restored
the current evidence, and rejected only the deliberately changed transport
source in the copy. These are actual process/file observations. The drift is
controlled, not a naturally discovered incident; no LLM task is counted.

## Contract and limit

A shared permitted checkout is required. The wire contains observations and
source fingerprints, not a complete copy of the repository. It is not the
3200-byte model experiment: the explicit transport cap here is **16,384 bytes**;
the retained run used **6090 bytes** including its pin. A plain shared file is
also a valid carrier for the same evidence.

The recorded source manifest covers inputs of these listed gates. A successful
check does not certify the whole project or authorize a publication. Hashes and
captured process exits rely on the trusted caller; they are not independent
attestation. The checks are sequential per-file observations, not an atomic
snapshot of a changing repository. Live admission needs its own concurrency
and authority contract.

This gives a reader a small operational use of the methodology: keep the
evidence for a conclusion, carry it across reset, then check whether its scope
and source still apply before reusing it.
