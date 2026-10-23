# Selected own-source induction evidence

[Finding and design](../PROGRAM_INDUCTION_STUDY.md) · [Українською](../PROGRAM_INDUCTION_STUDY.uk.md)

One developer-authored N=1 pilot: ten model calls, nine source generations,
100 saved executions and 156 weighted truth rows. Additional explicit
organization did not improve the registered transfer contrast. Fresh ordinary
induction scored better. The supplied diagnostic did not distinguish all
explicit alternatives already present in M0.

## Offline readback

From the repository root, Python 3.11+ standard library:

```sh
python3 -I -S -B research/program_induction/verify_projection.py
python3 -O -m unittest discover -s research/program_induction -p 'test_projection.py' -q
```

No network, model, candidate execution or import of archived code. Source
strings are untrusted **data**, never modules to load. The verifier recomputes
exact categorical Brier losses and the component/global agreement table from
the selected data. Regrading saved output does not reproduce its generation.

## Files and trust

- `projection.json.gz`: exact selected prompts, visible responses/carriers,
  usage, runtime request bytes and captured forecast outputs; authored cases
  and explicit registered score declarations.
- `projection-mapping.json`: original digests, selection and omissions.
- `verify_projection.py`: independent stdlib readback with embedded expected
  publication pins, bounded strict JSON and exact rational calculations.
- `test_projection.py`: malformed/tampered input and semantic counterexamples.

The local freeze preceded inference. It is not independent preregistration or
authentication. Full native CLI stdout/stderr was not retained by the original
transport. Only selected metadata is published. The projection is not the full
original source tree. Coherent replacement of both evidence and trusted verifier
is outside the integrity claim.

Source changes, observed forecast changes, predictive benefit and adequate
identification of a mechanism remain separate. No audit graph relations are
inferred from a good score; the ontology and claim ledger are unchanged.
