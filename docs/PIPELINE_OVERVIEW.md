# Pipeline Overview

Core skeleton (domain-agnostic):

raw -> extract -> build -> preprocess -> core -> report

Folders reflect this shape:

- core/: engine, heads, policy, signals (domain-agnostic)
- adapters/: curriculum & conversation preprocessors/streams (domain-specific hygiene)
- reporters/: shared and specialized reporters
- pipeline/
  - curriculum/: wrappers for curriculum scripts (normalize/build/run)
  - conversation/: wrappers for conversation scripts (scrub/build/run)
- scripts/: existing command-line tools (implementation details)

Use manifests/ to orchestrate raw-to-report runs. See `scripts/ingest_and_analyze.py`.

