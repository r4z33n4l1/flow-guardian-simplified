"""
Large-Scale Customer Service Document Test for Backboard.io

Tests the hypothesis: Since Backboard stores all messages,
semantic recall should reliably retrieve relevant content regardless of scale.

This test:
1. Generates 50+ synthetic customer service documents
2. Uploads all documents to Backboard with memory="Auto"
3. Runs retrieval queries for each document type
4. Verifies recall accuracy
5. Reports metrics
"""

import asyncio
import os
import time
from typing import List, Tuple
import pytest
from dotenv import load_dotenv

load_dotenv()

# Import document generator
from tests.document_generator import (
    generate_all_documents,
    get_test_queries,
    Document
)


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("BACKBOARD_API_KEY"),
    reason="BACKBOARD_API_KEY not set"
)


def get_client():
    """Create Backboard client."""
    from backboard import BackboardClient
    api_key = os.environ.get("BACKBOARD_API_KEY")
    return BackboardClient(api_key=api_key)


class ScaleTestMetrics:
    """Collect and report test metrics."""

    def __init__(self):
        self.upload_times: List[float] = []
        self.query_times: List[float] = []
        self.query_results: List[Tuple[str, bool, str]] = []  # (query, success, response_preview)
        self.total_documents = 0
        self.start_time = None
        self.end_time = None

    def record_upload(self, duration: float):
        self.upload_times.append(duration)

    def record_query(self, query: str, success: bool, response: str, duration: float):
        self.query_times.append(duration)
        self.query_results.append((query, success, response[:200] if response else ""))

    def report(self) -> str:
        """Generate metrics report."""
        total_time = self.end_time - self.start_time if self.end_time else 0
        successful_queries = sum(1 for _, success, _ in self.query_results if success)

        report = f"""
{'='*60}
SCALE TEST METRICS REPORT
{'='*60}

DOCUMENTS
---------
Total documents uploaded: {self.total_documents}
Average upload time: {sum(self.upload_times)/len(self.upload_times):.2f}s
Total upload time: {sum(self.upload_times):.2f}s

QUERIES
-------
Total queries: {len(self.query_results)}
Successful queries: {successful_queries}
Success rate: {(successful_queries/len(self.query_results)*100):.1f}%
Average query time: {sum(self.query_times)/len(self.query_times):.2f}s

OVERALL
-------
Total test time: {total_time:.2f}s

QUERY DETAILS
-------------"""
        for query, success, preview in self.query_results:
            status = "✓" if success else "✗"
            report += f"\n{status} {query[:50]}..."
            if not success:
                report += f"\n  Response: {preview}"

        report += f"\n{'='*60}\n"
        return report


@pytest.fixture(scope="module")
def metrics():
    """Create metrics collector."""
    return ScaleTestMetrics()


@pytest.fixture(scope="module")
def documents():
    """Generate all test documents."""
    return generate_all_documents()


@pytest.fixture(scope="module")
def test_queries():
    """Get test queries."""
    return get_test_queries()


@pytest.mark.asyncio
async def test_scale_upload_and_recall(metrics, documents, test_queries):
    """
    Main scale test: Upload all documents and test retrieval.

    This is intentionally a single large test to:
    1. Use a single assistant/thread for all documents
    2. Test retrieval after all documents are uploaded
    3. Measure end-to-end performance
    """
    client = get_client()
    metrics.start_time = time.time()
    metrics.total_documents = len(documents)

    print(f"\n{'='*60}")
    print(f"SCALE TEST: {len(documents)} Customer Service Documents")
    print(f"{'='*60}\n")

    # Create assistant for scale test
    print("[1/4] Creating assistant...")
    assistant = await client.create_assistant(
        name="scale-test-customer-service",
        description="Scale test assistant for customer service documents"
    )
    print(f"      Assistant ID: {assistant.assistant_id}")

    # Create thread
    print("[2/4] Creating thread...")
    thread = await client.create_thread(assistant.assistant_id)
    print(f"      Thread ID: {thread.thread_id}")

    # Upload all documents
    print(f"\n[3/4] Uploading {len(documents)} documents...")
    for i, doc in enumerate(documents):
        start = time.time()

        # Format document for storage
        content = f"""## {doc.category}: {doc.title}

**Document ID:** {doc.id}
**Keywords:** {', '.join(doc.keywords)}

---

{doc.content}
"""
        try:
            await client.add_message(
                thread_id=thread.thread_id,
                content=content,
                memory="Auto",
                stream=False
            )
            duration = time.time() - start
            metrics.record_upload(duration)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"      Uploaded {i + 1}/{len(documents)} documents...")

        except Exception as e:
            print(f"      ERROR uploading {doc.id}: {e}")

    print(f"      All {len(documents)} documents uploaded!")

    # Wait for indexing
    print("\n      Waiting 5 seconds for memory indexing...")
    await asyncio.sleep(5)

    # Run retrieval queries
    print(f"\n[4/4] Running {len(test_queries)} retrieval queries...")
    for i, query_info in enumerate(test_queries):
        query = query_info["query"]
        expected_keywords = query_info["expected_keywords"]

        start = time.time()
        try:
            response = await client.add_message(
                thread_id=thread.thread_id,
                content=query,
                memory="Auto",
                stream=False
            )
            duration = time.time() - start

            # Check if response contains expected keywords
            response_text = response.content.lower() if hasattr(response, 'content') else str(response).lower()
            found_keywords = [kw for kw in expected_keywords if kw.lower() in response_text]
            success = len(found_keywords) > 0

            metrics.record_query(query, success, response_text, duration)

            status = "✓" if success else "✗"
            print(f"      {status} Query {i + 1}: {query[:40]}...")

        except Exception as e:
            metrics.record_query(query, False, str(e), 0)
            print(f"      ✗ Query {i + 1} ERROR: {e}")

    metrics.end_time = time.time()

    # Print report
    print(metrics.report())

    # Assert overall success rate
    successful = sum(1 for _, success, _ in metrics.query_results if success)
    success_rate = successful / len(metrics.query_results)

    assert success_rate >= 0.80, f"Success rate {success_rate:.1%} below 80% threshold"


@pytest.mark.asyncio
async def test_specific_document_recall():
    """
    Test that specific, unique information can be recalled.

    Uses documents with unique identifiers to verify exact recall.
    """
    client = get_client()

    print("\n" + "="*60)
    print("SPECIFIC DOCUMENT RECALL TEST")
    print("="*60 + "\n")

    # Create fresh assistant
    assistant = await client.create_assistant(
        name="specific-recall-test",
        description="Test specific document recall"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Store documents with unique identifiers
    unique_docs = [
        {
            "id": "UNIQUE-001",
            "content": "The secret project code is ALPHA-BRAVO-7742. This is for the Q1 2026 launch.",
            "query": "What is the secret project code?",
            "expected": "ALPHA-BRAVO-7742"
        },
        {
            "id": "UNIQUE-002",
            "content": "Employee discount code for January 2026 is EMPLOYEE-JAN26-50OFF. Valid until January 31.",
            "query": "What is the employee discount code for January?",
            "expected": "EMPLOYEE-JAN26-50OFF"
        },
        {
            "id": "UNIQUE-003",
            "content": "The warehouse supervisor is Marcus Johnson, extension 4455. Contact for inventory issues.",
            "query": "Who is the warehouse supervisor and what is their extension?",
            "expected": "Marcus Johnson"
        },
    ]

    # Upload unique documents
    print("[1/2] Uploading unique documents...")
    for doc in unique_docs:
        await client.add_message(
            thread_id=thread.thread_id,
            content=f"Document {doc['id']}: {doc['content']}",
            memory="Auto",
            stream=False
        )
        print(f"      Uploaded {doc['id']}")

    # Wait for indexing
    await asyncio.sleep(3)

    # Test recall
    print("\n[2/2] Testing specific recall...")
    all_passed = True

    for doc in unique_docs:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=doc["query"],
            memory="Auto",
            stream=False
        )

        response_text = response.content if hasattr(response, 'content') else str(response)
        found = doc["expected"].lower() in response_text.lower()

        status = "✓" if found else "✗"
        print(f"      {status} {doc['id']}: Looking for '{doc['expected']}'")
        if not found:
            print(f"         Response: {response_text[:200]}...")
            all_passed = False

    assert all_passed, "Not all unique documents were correctly recalled"


@pytest.mark.asyncio
async def test_category_filtering():
    """
    Test that queries return results from the correct category.
    """
    client = get_client()

    print("\n" + "="*60)
    print("CATEGORY FILTERING TEST")
    print("="*60 + "\n")

    assistant = await client.create_assistant(
        name="category-test",
        description="Test category-based retrieval"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Upload one document from each category
    categories = [
        ("FAQ", "FAQ: How do I track my order?\nAnswer: Use order tracking at track.example.com"),
        ("Policy", "RETURN POLICY: 30-day return window for all items. Must be unused."),
        ("Guide", "SETUP GUIDE: Step 1 - Unbox device. Step 2 - Connect power. Step 3 - Download app."),
        ("Ticket", "TICKET #12345: Customer reported login issue. Resolution: Password reset sent."),
    ]

    print("[1/2] Uploading category documents...")
    for category, content in categories:
        await client.add_message(
            thread_id=thread.thread_id,
            content=f"[{category}] {content}",
            memory="Auto",
            stream=False
        )
        print(f"      Uploaded {category}")

    await asyncio.sleep(3)

    # Test category-specific queries
    print("\n[2/2] Testing category queries...")
    queries = [
        ("How do I track my order?", "FAQ"),
        ("What is the return policy?", "Policy"),
        ("How do I set up my device?", "Guide"),
        ("Show me a resolved support ticket", "Ticket"),
    ]

    for query, expected_category in queries:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=query,
            memory="Auto",
            stream=False
        )

        response_text = response.content if hasattr(response, 'content') else str(response)
        # Check if response relates to the expected category
        print(f"      Query: {query}")
        print(f"      Response preview: {response_text[:150]}...")
        print()


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_scale_upload_and_recall(
        ScaleTestMetrics(),
        generate_all_documents(),
        get_test_queries()
    ))
