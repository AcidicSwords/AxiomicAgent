"""
Test conversation health tracker with realistic multi-turn scenarios.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import time
from conversation_health_tracker import ConversationHealthTracker, example_integration_hook


def simulate_conversation(name: str, exchanges: list):
    """Simulate a multi-turn conversation."""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}\n")

    tracker = ConversationHealthTracker()

    for i, (user_msg, assistant_msg) in enumerate(exchanges, 1):
        print(f"Turn {i}:")
        print(f"  User: {user_msg[:80]}...")
        print(f"  Assistant: {assistant_msg[:80]}...")

        guidance = example_integration_hook(user_msg, assistant_msg, tracker)

        if guidance:
            print(f"\n  ⚠ GUIDANCE TRIGGERED:")
            for line in guidance.split('\n'):
                print(f"    {line}")

        print()
        time.sleep(0.1)  # Small delay between turns

    # Final summary
    print(f"\n  FINAL SUMMARY:")
    summary = tracker.generate_coaching_summary()
    for line in summary.split('\n'):
        print(f"    {line}")
    print()


def main():
    # Test 1: Prince Andrew Evasion Pattern
    evasion_exchanges = [
        (
            "Why did you decide to deploy on Friday afternoon?",
            "Well, deployment timing is a complex topic. There are many considerations in modern DevOps practices."
        ),
        (
            "But specifically, why Friday at 4pm?",
            "Let me explain our deployment pipeline architecture. We use continuous deployment with automated testing..."
        ),
        (
            "I'm asking specifically about THIS deployment timing decision.",
            "The team follows best practices. We have staging environments, rollback procedures, and monitoring in place."
        ),
    ]

    simulate_conversation("Prince Andrew Evasion Pattern (Accountability Context)", evasion_exchanges)

    # Test 2: Rogers-Gloria Exploration Pattern
    exploration_exchanges = [
        (
            "I'm thinking about our database design... maybe we need normalization? Or would denormalization be better for our use case?",
            "Let's explore both directions. What kind of queries are you running most often?"
        ),
        (
            "Mostly reads, but sometimes complex joins. I'm also wondering if we should cache...",
            "Interesting. So you're balancing read performance with data consistency. Caching could help, but let's think about where - application level or database level?"
        ),
        (
            "Maybe Redis? Or should we use the built-in query cache? I'm also thinking about sharding...",
            "You're exploring several optimization paths - caching, query optimization, and scaling. Each addresses different bottlenecks. What's your current main pain point?"
        ),
    ]

    simulate_conversation("Rogers-Gloria Exploration Pattern (Exploratory Context)", exploration_exchanges)

    # Test 3: Apollo 13 Crisis Pattern
    crisis_exchanges = [
        (
            "URGENT: Production is returning 500 errors on all API endpoints",
            "Let me check the error logs immediately. Can you confirm - are you seeing this across all endpoints or specific ones?"
        ),
        (
            "All endpoints. Started 5 minutes ago.",
            "Checking server status now. Database connections: OK. Let me verify the application server logs. Do you see any recent deployments in the last 10 minutes?"
        ),
        (
            "Yes, we deployed authentication changes at 14:23 UTC",
            "Found it - authentication middleware is rejecting all requests. Error: 'Token validation failed - secret key mismatch'. Rolling back authentication deployment now."
        ),
    ]

    simulate_conversation("Apollo 13 Crisis Pattern (Crisis Context)", crisis_exchanges)

    # Test 4: Trump-Biden Chaos Pattern
    chaos_exchanges = [
        (
            "The login form isn't working",
            "Let's look at the form validation code in the frontend React component..."
        ),
        (
            "Also the database seems slow",
            "We should check the database indexes. Also, are you using connection pooling?"
        ),
        (
            "And the deployment pipeline failed yesterday",
            "The CI/CD configuration might need updating. Also, have you checked the Docker image sizes?"
        ),
        (
            "Wait, what about the login form?",
            "Right, the login form. We also need to look at the API endpoint, the authentication middleware, and the session management..."
        ),
    ]

    simulate_conversation("Trump-Biden Chaos Pattern (Fragmented Context)", chaos_exchanges)

    # Test 5: Direct and Helpful (Ideal Pattern)
    ideal_exchanges = [
        (
            "Why is my React component re-rendering constantly?",
            "Your component is re-rendering because you're creating a new object in the render method on line 42. This creates a new reference each time. Solution: Move the object creation outside render or use useMemo. Want me to show you the code change?"
        ),
        (
            "Yes please, show me the fix",
            "Here's the fix:\n\nBefore:\nfunction MyComponent() {\n  const config = {theme: 'dark'}; // New object each render\n  return <Child config={config} />;\n}\n\nAfter:\nconst config = {theme: 'dark'}; // Outside component\nfunction MyComponent() {\n  return <Child config={config} />;\n}\n\nThis creates the object once instead of on every render. Does this make sense?"
        ),
        (
            "Perfect, that fixed it! Thanks",
            "Great! The key principle is that React compares props by reference, not value. Any new object triggers a re-render. Feel free to ask if you hit similar issues."
        ),
    ]

    simulate_conversation("Ideal Pattern (Direct and Helpful)", ideal_exchanges)


if __name__ == "__main__":
    print("="*80)
    print("CONVERSATION HEALTH TRACKER - COMPREHENSIVE TESTING")
    print("="*80)
    print()
    print("Testing against historical conversation patterns:")
    print("  1. Prince Andrew (Evasion)")
    print("  2. Rogers-Gloria (Healthy Exploration)")
    print("  3. Apollo 13 (Crisis Precision)")
    print("  4. Trump-Biden (Chaos/Fragmentation)")
    print("  5. Ideal (Direct and Helpful)")
    print()

    main()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
