# Generic-file control and capacity boundary

This is an offline post-cohort software replay on the repair study's already
used eight source instances. It makes **zero model calls**. It does not provide
new held-out model results or independent scientific validation.

## Result

| Source variant, eight each | Full ordinary file preserves history | Codec fits 3200 bytes | Same receiver prompt when admitted |
|---|---:|---:|---:|
| Original source | 8/8 | 8/8 | 8/8 |
| Eight repeated 512-character log records added | 8/8 | 8/8 | 8/8 |
| Eight deterministic variable 512-character log records added | 8/8 | 0/8 | Not admitted |

Each wire budget includes the 64 ASCII bytes of its external SHA-256 pin.
Uncompressed ordinary files plus their pin take 15,687 bytes for the original
source and 21,935 after added logs; they do not fit this particular narrow
channel. If a shared file or larger storage channel is permitted, the file
already retains the required information. The codec has no demonstrated
advantage over that information-equivalent access.

For every admitted codec case, actual file readback and decoded canonical bytes
are equal. Receiver prompts are byte-identical. This establishes input parity,
not a new 8/8 model-performance score for the generic file. Model inference was
not rerun, and possible output nondeterminism is not measured here.

Variable logs make the codec exceed capacity in all eight cases. The adapter
raises `complete-handoff-exceeds-capacity` without truncation, fallback retrieval
or inference. Repetitive logs fitting and equally long variable logs failing
demonstrate dependence on compressibility, not semantic relevance.

## Reproduce

```sh
python3 -m unittest discover -s research/handoff_controls -q
python3 research/handoff_controls/study.py
```

The first command is read-only except for its own temporary files. The second
regenerates `results.json` deterministically, with source hashes and every case.
No services, providers or generated code are invoked.
