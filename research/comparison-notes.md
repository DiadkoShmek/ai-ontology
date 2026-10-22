# Source check of an external comparison

Checked 22 October 2026. This is a bounded source review, not a full audit of another system or a ranking of authors. External code was read, not installed or executed.

## Saluca Labs / pr0fx

The original post [I Have a Self. The Lights Are Off.](https://www.saluca.com/p/i-have-a-self-the-lights-are-off) (14 August 2026) describes `/shi/pr0fx` as running and claims a sealed constitution and a hash-chained history. This establishes what its publisher reports; this review did not independently inspect that running instance or reproduce a behavioral result.

There is public engineering material. The [Tiresias repository](https://github.com/saluca-labs/tiresias-core/tree/3c634b6e5bec18b685d35d95f7080d9aee955598) was inspected at tree `3c634b6e5bec18b685d35d95f7080d9aee955598`. The [SOP event logger](https://github.com/saluca-labs/tiresias-core/blob/3c634b6e5bec18b685d35d95f7080d9aee955598/src/tiresias/audit/logger.py) and [storage schema](https://github.com/saluca-labs/tiresias-core/blob/3c634b6e5bec18b685d35d95f7080d9aee955598/src/tiresias/storage/schema.py) provide concrete logging/storage implementation. Those two files do not by themselves verify pr0fx's full claimed lifecycle. Their limited inspection is not evidence that mechanisms elsewhere are absent.

## Ziegler / RLM attribution

[Gabe Ziegler's original memory guide](https://gabrielis.me/blog/second-brain-guide/) describes Supabase/Postgres storage, MCP tools, document search and GitHub backup. It is a concrete relevant memory architecture. This review did not establish that Gabe is the Ziegler intended by the supplied comparison, or find the particular claimed RLM synthesis.

The primary [Recursive Language Models paper](https://arxiv.org/abs/2512.24601v3) is by Alex L. Zhang, Tim Kraska and Omar Khattab. It describes programmatic interaction with external context and recursive model calls. This does not rule out a separate Ziegler application or synthesis; that exact attribution remains unresolved. No invented citation is included in the book.

## Consequence for this edition

The criticism correctly exposed an inadequate public engineering account in v2.0.0: the included implementation was only an in-memory reducer. Version 2.1.0 adds an actual durable runtime, a model adapter seam, reproducible process tests and a technical chapter. These additions do not retrospectively create LLM trials or independently validate anyone's identity claims.

Compare separate dimensions: conceptual coverage, executable mechanism, inspected runtime, systems tests, controlled model behavior and human benefit. Public source, a running-instance report and an empirical comparison are different kinds of evidence.
