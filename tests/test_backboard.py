"""
Pytest tests for Backboard.io SDK integration.

Run with: pytest tests/ -v

These tests verify the core Backboard functionality:
- Creating assistants
- Creating threads
- Storing messages
- Memory recall
"""

import asyncio
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# Skip all tests if API key not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("BACKBOARD_API_KEY"),
    reason="BACKBOARD_API_KEY not set"
)


def get_client():
    """Create Backboard client."""
    from backboard import BackboardClient
    api_key = os.environ.get("BACKBOARD_API_KEY")
    return BackboardClient(api_key=api_key)


@pytest.mark.asyncio
async def test_create_assistant():
    """Test creating a Backboard assistant."""
    client = get_client()
    assistant = await client.create_assistant(
        name="pytest-test-assistant",
        description="Test assistant for pytest"
    )

    assert assistant is not None
    assert hasattr(assistant, 'assistant_id')
    assert assistant.assistant_id is not None


@pytest.mark.asyncio
async def test_create_thread():
    """Test creating a thread within an assistant."""
    client = get_client()

    # Create assistant first
    assistant = await client.create_assistant(
        name="pytest-thread-test",
        description="Test assistant for thread creation"
    )

    # Create thread
    thread = await client.create_thread(assistant.assistant_id)

    assert thread is not None
    assert hasattr(thread, 'thread_id')
    assert thread.thread_id is not None


@pytest.mark.asyncio
async def test_store_message():
    """Test storing a message in a thread."""
    client = get_client()

    # Create assistant and thread
    assistant = await client.create_assistant(
        name="pytest-message-test",
        description="Test assistant for message storage"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Store message
    response = await client.add_message(
        thread_id=thread.thread_id,
        content="Test context: Working on authentication module.",
        memory="Auto",
        stream=False
    )

    assert response is not None
    assert hasattr(response, 'content') or hasattr(response, 'message_id')


@pytest.mark.asyncio
async def test_memory_recall():
    """Test storing context and then recalling it with memory='Auto'."""
    client = get_client()

    # Create assistant and thread
    assistant = await client.create_assistant(
        name="pytest-memory-test",
        description="Test assistant for memory recall"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Store specific context
    context = """## Test Context
**Project:** Flow Guardian
**Task:** Testing memory recall functionality
**Important note:** The secret code is PYTEST123
"""

    await client.add_message(
        thread_id=thread.thread_id,
        content=context,
        memory="Auto",
        stream=False
    )

    # Wait for indexing
    await asyncio.sleep(2)

    # Recall the context
    recall_response = await client.add_message(
        thread_id=thread.thread_id,
        content="What is the secret code I mentioned?",
        memory="Auto",
        stream=False
    )

    assert recall_response is not None
    assert hasattr(recall_response, 'content')
    print(f"Recall response: {recall_response.content}")


@pytest.mark.asyncio
async def test_multiple_context_storage():
    """Test storing multiple pieces of context."""
    client = get_client()

    # Create assistant and thread
    assistant = await client.create_assistant(
        name="pytest-multi-context-test",
        description="Test assistant for multiple context storage"
    )
    thread = await client.create_thread(assistant.assistant_id)

    contexts = [
        "Learning 1: Always use UTC for timestamps in distributed systems.",
        "Learning 2: JWT tokens should have short expiry times (15 min max).",
        "Learning 3: Refresh tokens should be rotated on each use.",
    ]

    for ctx in contexts:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=ctx,
            memory="Auto",
            stream=False
        )
        assert response is not None

    # Wait for indexing
    await asyncio.sleep(2)

    # Query about the learnings
    recall = await client.add_message(
        thread_id=thread.thread_id,
        content="What learnings do I have about JWT tokens?",
        memory="Auto",
        stream=False
    )

    assert recall is not None
    print(f"Multi-context recall: {recall.content}")
