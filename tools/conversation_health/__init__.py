"""
Optional conversation health tracker add-on.

This module is intentionally standalone and has no side effects when
imported. It provides a lightweight, prompt-aligned tracker to flag
patterns like accountability evasion, fragmentation, and topic
coherence issues during conversations.

Dependencies:
- Pure Python by default
- Optional: sentence-transformers (only if drift_on_specifics is used)

Usage (standalone):
    from tools.conversation_health.tracker import ConversationHealthTracker
    tracker = ConversationHealthTracker()
    tracker.add_turn('user', 'Why did the test fail?')
    health = tracker.add_turn('assistant', 'Let me explain testing...')
    print(health)

This add-on is not used unless explicitly enabled (e.g., via a CLI flag).
"""

