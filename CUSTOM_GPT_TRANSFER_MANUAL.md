# Guide for Transferring the Program to a Custom GPT Layer

This manual bundles the key artifacts your custom GPT developer will need:

1. **High-level architecture** (pipeline/orchestrator, conversation parsing, metrics).
2. **Execution recipes** (parse → build → health → combine, with best-of settings).
3. **Optional add-on** (conversation health tracker + context flag generation).
4. **Integration cues** (where to read metrics, how to include context_flags/QA data, prompts to append).

## Core steps
- Run `python -m pipeline.run --manifest manifests/curriculum_conversation_example.json` with `AXIOM_FAISS_ENABLED=1` to refresh YouTube/MIT datasets.
- Re-parse conversation transcripts with `python -m pipeline.conversation.parse_turns --chunk-size 3`.
- Rebuild conversation health with `python -m pipeline.conversation.run_health --window 12 --force --context-flags` and inspect `reports/conversation_insight_fs/*.metrics.json`.
- Execute `python -m pipeline.reporting.combine_reports --curriculum-insights reports/mit_curriculum_insights_fs --curriculum-dynamics reports/mit_curriculum_dynamics_fs --conversation-insights reports/conversation_insight_fs --conversation-dynamics reports/conversation_dynamics_fs --out-dir reports/comprehensive` for merged outputs.

## Key outputs
- `reports/conversation_insight_fs/*_parsed.metrics.json` (health metrics + QA + optional context_flags)
- `reports/comprehensive/combined.json` + `.md` (summary, sidecars units/topics)
- `tools/conversation_health/tracker.py` (runtime tracking for alerts/guidance)
- `CUSTOM_GPT_INTEGRATION.md` (instructions for GPT builder)

## Integration tips
- Feed `summary.context_flags` into your custom GPT prompts (status, alerts, guidance).
- Use `summary.qa` to monitor zero-node/zero-edge fractions and turn counts.
- For live guidance, import `tools.conversation_health.tracker.ConversationHealthTracker` and call `generate_coaching_summary()` when alerts exist.
- Append relevant sections of `CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md` to system messages for patterned responses.

## Packaging
- This manual + `pipeline/`, `tools/conversation_health`, `docs/`, `custom GPT integration docs` and `reports/comprehensive` are zipped into the transfer artifact for the custom GPT builder.
