# Preflight repair before the first inference

The first run refused at `model-drift` before warm-up or any scored request.
Ollama `/api/show` presents identical parameter entries in varying map order.
Hashing that presentation as an ordered string created a false drift report.

The observer now sorts complete parameter lines before hashing. Model bundle
digest, template hash and every actual generation option remain pinned. The
first freeze is retained as `preflight-v1-freeze.json`. A new freeze and local
commit were made before inference. No cases, gold, prompts, scoring or budgets
were changed after observing model responses: there were no responses yet.
