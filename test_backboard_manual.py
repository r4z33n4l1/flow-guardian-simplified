#!/usr/bin/env python3
"""
Manual test script for Backboard.io SDK exploration.

Run with: python test_backboard_manual.py

This script walks through the Backboard SDK to understand:
1. Creating assistants
2. Creating threads
3. Storing context (messages)
4. Retrieving context with memory="Auto" (semantic recall)
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    from backboard import BackboardClient

    api_key = os.environ.get("BACKBOARD_API_KEY")
    if not api_key:
        print("ERROR: BACKBOARD_API_KEY not set in environment")
        return

    print("=" * 60)
    print("Backboard.io SDK Test")
    print("=" * 60)

    # Initialize client
    print("\n[1] Initializing BackboardClient...")
    client = BackboardClient(api_key=api_key)
    print("    Client initialized successfully")

    # Create an assistant
    print("\n[2] Creating assistant 'flow-guardian-test'...")
    assistant = await client.create_assistant(
        name="flow-guardian-test",
        description="Assistant for testing Flow Guardian context memory"
    )
    print(f"    Assistant created!")
    print(f"    - ID: {assistant.assistant_id}")

    # Create a thread
    print("\n[3] Creating thread...")
    thread = await client.create_thread(assistant.assistant_id)
    print(f"    Thread created!")
    print(f"    - ID: {thread.thread_id}")

    # Store a context message (simulating capture)
    print("\n[4] Storing context message (simulating flow capture)...")
    context_message = """## Context Snapshot
**Working on:** Implementing JWT authentication for the API
**Branch:** feature/jwt-auth
**Key files:** src/auth.py, src/middleware.py, tests/test_auth.py
**Hypothesis:** The token expiry check might be using local time instead of UTC
**Next steps:**
- Fix the timezone handling in token validation
- Add unit tests for expiry edge cases
- Update the refresh token endpoint
"""

    # Store without LLM response (just save to memory)
    response1 = await client.add_message(
        thread_id=thread.thread_id,
        content=context_message,
        memory="Auto",  # Enable memory storage
        stream=False
    )
    print(f"    Context stored!")
    print(f"    - Message ID: {response1.message_id if hasattr(response1, 'message_id') else 'N/A'}")
    print(f"    - Response content (truncated): {str(response1.content)[:200] if hasattr(response1, 'content') else 'N/A'}...")

    # Wait a moment for memory indexing
    print("\n    Waiting 2 seconds for memory indexing...")
    await asyncio.sleep(2)

    # Store another piece of context
    print("\n[5] Storing a learning...")
    learning_message = """**Learning:** JWT tokens should always use UTC timestamps.
The datetime.utcnow() function is deprecated in Python 3.12+, use datetime.now(timezone.utc) instead.
Tags: jwt, python, timezone, auth
"""

    response2 = await client.add_message(
        thread_id=thread.thread_id,
        content=learning_message,
        memory="Auto",
        stream=False
    )
    print(f"    Learning stored!")

    # Wait for indexing
    await asyncio.sleep(2)

    # Now test retrieval with memory="Auto"
    print("\n[6] Testing memory recall (asking what we were working on)...")
    recall_response = await client.add_message(
        thread_id=thread.thread_id,
        content="What was I working on? What were the key files and next steps?",
        memory="Auto",  # This triggers semantic search
        stream=False
    )
    print(f"    Recall response:")
    print("-" * 40)
    if hasattr(recall_response, 'content'):
        print(recall_response.content)
    else:
        print(recall_response)
    print("-" * 40)

    # Test specific recall
    print("\n[7] Testing specific recall (JWT timezone issue)...")
    specific_recall = await client.add_message(
        thread_id=thread.thread_id,
        content="What did I learn about JWT and timezones?",
        memory="Auto",
        stream=False
    )
    print(f"    Specific recall response:")
    print("-" * 40)
    if hasattr(specific_recall, 'content'):
        print(specific_recall.content)
    else:
        print(specific_recall)
    print("-" * 40)

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Assistant ID: {assistant.assistant_id}")
    print(f"  - Thread ID: {thread.thread_id}")
    print(f"\nYou can reuse these IDs to continue testing.")


if __name__ == "__main__":
    asyncio.run(main())
