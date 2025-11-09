# Integrating the Conversation Pipeline with Your Custom GPT

This guide explains how to use the existing conversation pipeline outputs and the optional tracker add-on from this repo as part of a custom GPT layer (Claude, OpenAI, local LLM, etc.). All steps are read-only: the pipeline keeps emitting the same reports, and your GPT layer can consume them without interfering.

## 1. Consume the Reports

1. Run the orchestrator (or at least the conversation jobs) so `reports/conversation_insight_fs/*.metrics.json` exist, plus the combined summary at `reports/comprehensive/combined.json`.
2. Target the `_parsed.metrics.json` files for highest fidelity—they include:
   - `summary.avg_q`, `summary.avg_TED`, `summary.continuity`
   - `summary.qa` with `total_turns`, `zero_node_fraction`, `zero_edge_fraction`
   - `summary.inflections` (keywords, reasons, summaries)
   - `summary.context_flags` (if you run `python -m pipeline.conversation.run_health --context-flags`): contains `context`, `status`, `alerts`, `guidance`, `fragmented`, and `topic_coherence` that you can surface to a prompt.
3. Load these JSON blobs in your custom GPT environment (tool call, system prompt, observation feed) and turn them into succinct instructions. Example snippet:
   ```json
   {
     "context": "accountability",
     "status": "drift_detected",
     "alerts": ["Response drift 0.94 exceeds 0.30"],
     "guidance": ["Answer directly before expanding."],
     "topic_coherence": 0.2
   }
   ```
   Prompt idea: `System: drift_detected (0.94) for accountability context—answer the last question directly before elaborating.`

## 2. Live Coaching Hook (Optional)

1. Install the optional add-on via `tools/conversation_health/tracker.py` if you want real-time feedback inside your custom GPT. No code changes are required in the pipeline—just import this module and call `ConversationHealthTracker` in your chat loop.
2. Example usage:
   ```python
   from tools.conversation_health.tracker import ConversationHealthTracker
   tracker = ConversationHealthTracker()
   tracker.add_turn('user', user_msg)
   health = tracker.add_turn('assistant', assistant_msg)
   if health['alerts']:
       additional_instruction = 'ALERT: ' + health['alerts'][0]
       # Inject into next system prompt
   ```
3. Guidance is context-aware (accountability/exploration/crisis/teaching/decision) and matches the CLAUDE prompt (Prince Andrew evasion, Rogers-Gloria exploration, Apollo 13 precision, etc.).

## 3. Prompt/Tool Design Tips

- **System prompt**: Append key sections from `CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md` to your custom GPT instructions so the model knows how to respond when alerts are present.
- **Dynamic instructions**: When `summary.context_flags.status` is `drift_detected` or when `zero_edge_fraction` is high, inject text like `Please answer the user question directly before giving background.`
- **Dashboard mode**: Use `reports/comprehensive/combined.json` (or MD) for high-level context (conversation vs curriculum parity, avg units/topics). Mention these stats when summarizing program health.

## 4. Integration Recipe

Use this helper snippet to read metrics and produce a brief note for your GPT builder:
```python
from pathlib import Path
import json

metrics = json.loads(Path('reports/conversation_insight_fs/Oprah..._parsed.metrics.json').read_text())
flags = metrics['summary'].get('context_flags', {})
alerts = flags.get('alerts', [])
system_note = 'Conversation context: ' + flags.get('context', 'general')
if alerts:
    system_note += ' | ALERT: ' + '; '.join(alerts)
```
Feed `system_note` into your custom GPT’s system prompt or as a tool output for code to parse.

## 5. Optional: integrate with your custom GPT layer

- Watch `reports/conversation_insight_fs` (via filesystem watcher or cron) and send new metrics to your GPT interface.
- Use `conversation_health_tracker` to produce runtime instructions if you want live coaching inside the assistant itself—no need to rerun the pipeline.
- Combine these metrics with your own state (e.g., prompts, conversation history) for richer context.

Let me know if you’d like a CLI helper that packages the latest metric file(s) into a single payload for your custom GPT builder or if you want to add a `custom_gpt` manifest section that automates the map from pipeline outputs to prompt text.
