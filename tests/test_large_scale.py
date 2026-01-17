"""
Large-Scale Backboard.io Test Suite

Combined test runner that:
1. Runs customer service document tests
2. Runs SQLite codebase tests
3. Collects comprehensive metrics
4. Generates final report

Run with: python3 -m pytest tests/test_large_scale.py -v -s
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import pytest
from dotenv import load_dotenv

load_dotenv()


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("BACKBOARD_API_KEY"),
    reason="BACKBOARD_API_KEY not set"
)


class ComprehensiveMetrics:
    """Comprehensive metrics collector for all tests."""

    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()

    def record_test(self, test_name: str, metrics: Dict[str, Any]):
        self.test_results[test_name] = metrics

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0

        report = f"""
{'#'*70}
#                    BACKBOARD.IO LARGE-SCALE TEST REPORT
{'#'*70}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {total_duration:.2f} seconds

{'='*70}
                            TEST SUMMARY
{'='*70}
"""
        total_docs = 0
        total_queries = 0
        total_successful = 0

        for test_name, metrics in self.test_results.items():
            docs = metrics.get('documents', 0)
            queries = metrics.get('queries', 0)
            successful = metrics.get('successful', 0)
            success_rate = (successful / queries * 100) if queries > 0 else 0

            total_docs += docs
            total_queries += queries
            total_successful += successful

            report += f"""
{test_name}
{'-'*len(test_name)}
  Documents uploaded: {docs}
  Queries executed: {queries}
  Successful queries: {successful}
  Success rate: {success_rate:.1f}%
  Duration: {metrics.get('duration', 0):.2f}s
"""

        overall_rate = (total_successful / total_queries * 100) if total_queries > 0 else 0

        report += f"""
{'='*70}
                          OVERALL STATISTICS
{'='*70}

Total Documents Uploaded: {total_docs}
Total Queries Executed: {total_queries}
Total Successful Queries: {total_successful}
Overall Success Rate: {overall_rate:.1f}%

{'='*70}
                            HYPOTHESIS TEST
{'='*70}

Hypothesis: "Since Backboard stores all messages, semantic recall
             should reliably retrieve relevant content regardless of scale."

Result: {"SUPPORTED" if overall_rate >= 80 else "NEEDS INVESTIGATION"}
        Overall success rate of {overall_rate:.1f}% {"meets" if overall_rate >= 80 else "does not meet"} 80% threshold.

{'='*70}
                           RECOMMENDATIONS
{'='*70}
"""

        if overall_rate >= 90:
            report += """
✓ Excellent performance! The system reliably recalls stored content.
  - Consider increasing scale for further stress testing
  - Document retrieval patterns for production use
"""
        elif overall_rate >= 80:
            report += """
✓ Good performance. System meets reliability threshold.
  - Review failed queries for patterns
  - Consider adjusting query phrasing for better recall
"""
        elif overall_rate >= 60:
            report += """
⚠ Moderate performance. Some queries not returning expected results.
  - Analyze failed query categories
  - Check if content is being properly indexed
  - Consider chunking large documents differently
"""
        else:
            report += """
✗ Performance below expectations.
  - Investigate indexing delay issues
  - Review document formatting
  - Check API rate limits
  - Consider smaller batch uploads
"""

        report += f"""
{'#'*70}
#                         END OF REPORT
{'#'*70}
"""
        return report


def get_client():
    """Create Backboard client."""
    from backboard import BackboardClient
    api_key = os.environ.get("BACKBOARD_API_KEY")
    return BackboardClient(api_key=api_key)


@pytest.fixture(scope="module")
def global_metrics():
    """Global metrics collector."""
    metrics = ComprehensiveMetrics()
    metrics.start()
    yield metrics
    metrics.end()
    print(metrics.generate_report())


@pytest.mark.asyncio
async def test_quick_sanity_check(global_metrics):
    """
    Quick sanity check before running large tests.
    Verifies API connectivity and basic functionality.
    """
    print(f"\n{'='*60}")
    print("SANITY CHECK: Basic API Functionality")
    print(f"{'='*60}\n")

    client = get_client()
    start = time.time()

    # Test assistant creation
    print("[1/4] Creating test assistant...")
    assistant = await client.create_assistant(
        name="sanity-check",
        description="Quick sanity check"
    )
    assert assistant.assistant_id, "Failed to create assistant"
    print(f"      ✓ Assistant created: {assistant.assistant_id}")

    # Test thread creation
    print("[2/4] Creating test thread...")
    thread = await client.create_thread(assistant.assistant_id)
    assert thread.thread_id, "Failed to create thread"
    print(f"      ✓ Thread created: {thread.thread_id}")

    # Test message storage
    print("[3/4] Storing test message...")
    response = await client.add_message(
        thread_id=thread.thread_id,
        content="Test message: The quick brown fox jumps over the lazy dog.",
        memory="Auto",
        stream=False
    )
    assert response, "Failed to store message"
    print("      ✓ Message stored")

    # Test recall
    print("[4/4] Testing recall...")
    await asyncio.sleep(2)
    recall = await client.add_message(
        thread_id=thread.thread_id,
        content="What animal jumped over the dog?",
        memory="Auto",
        stream=False
    )
    response_text = recall.content.lower() if hasattr(recall, 'content') else str(recall).lower()
    found = "fox" in response_text
    print(f"      {'✓' if found else '✗'} Recall {'successful' if found else 'failed'}")

    duration = time.time() - start
    global_metrics.record_test("Sanity Check", {
        "documents": 1,
        "queries": 1,
        "successful": 1 if found else 0,
        "duration": duration
    })

    print(f"\n      Duration: {duration:.2f}s")
    assert found, "Basic recall test failed"


@pytest.mark.asyncio
async def test_medium_scale_documents(global_metrics):
    """
    Medium-scale test with ~40 documents.
    Tests core retrieval functionality at moderate scale.
    """
    from tests.document_generator import generate_all_documents, get_test_queries

    print(f"\n{'='*60}")
    print("MEDIUM SCALE TEST: Customer Service Documents")
    print(f"{'='*60}\n")

    client = get_client()
    start = time.time()

    # Get documents (limit to 40 for medium test)
    all_docs = generate_all_documents()
    docs = all_docs[:40]  # Take first 40

    print(f"Testing with {len(docs)} documents\n")

    # Create assistant
    print("[1/4] Creating assistant...")
    assistant = await client.create_assistant(
        name="medium-scale-test",
        description="Medium scale document test"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Upload documents
    print(f"[2/4] Uploading {len(docs)} documents...")
    for i, doc in enumerate(docs):
        content = f"## {doc.category}: {doc.title}\n\n{doc.content}"
        await client.add_message(
            thread_id=thread.thread_id,
            content=content,
            memory="Auto",
            stream=False
        )
        if (i + 1) % 10 == 0:
            print(f"      Uploaded {i + 1}/{len(docs)}")

    print("      Waiting for indexing...")
    await asyncio.sleep(5)

    # Run queries
    queries = get_test_queries()[:10]  # Test with 10 queries
    print(f"\n[3/4] Running {len(queries)} queries...")

    successful = 0
    for q in queries:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=q["query"],
            memory="Auto",
            stream=False
        )
        response_text = response.content.lower() if hasattr(response, 'content') else ""
        if any(kw.lower() in response_text for kw in q["expected_keywords"]):
            successful += 1
            print(f"      ✓ {q['query'][:40]}...")
        else:
            print(f"      ✗ {q['query'][:40]}...")

    duration = time.time() - start
    success_rate = successful / len(queries) * 100

    global_metrics.record_test("Medium Scale (40 docs)", {
        "documents": len(docs),
        "queries": len(queries),
        "successful": successful,
        "duration": duration
    })

    print(f"\n[4/4] Results:")
    print(f"      Success rate: {success_rate:.1f}%")
    print(f"      Duration: {duration:.2f}s")

    assert success_rate >= 70, f"Success rate {success_rate}% below threshold"


@pytest.mark.asyncio
async def test_full_scale_documents(global_metrics):
    """
    Full-scale test with all generated documents (~80).
    """
    from tests.document_generator import generate_all_documents, get_test_queries

    print(f"\n{'='*60}")
    print("FULL SCALE TEST: All Customer Service Documents")
    print(f"{'='*60}\n")

    client = get_client()
    start = time.time()

    docs = generate_all_documents()
    print(f"Testing with ALL {len(docs)} documents\n")

    # Create assistant
    print("[1/4] Creating assistant...")
    assistant = await client.create_assistant(
        name="full-scale-test",
        description="Full scale document test"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Upload all documents
    print(f"[2/4] Uploading {len(docs)} documents...")
    for i, doc in enumerate(docs):
        content = f"## {doc.category}: {doc.title}\n\nID: {doc.id}\nKeywords: {', '.join(doc.keywords)}\n\n{doc.content}"
        await client.add_message(
            thread_id=thread.thread_id,
            content=content,
            memory="Auto",
            stream=False
        )
        if (i + 1) % 20 == 0:
            print(f"      Uploaded {i + 1}/{len(docs)}")

    print("      Waiting for indexing...")
    await asyncio.sleep(8)

    # Run all queries
    queries = get_test_queries()
    print(f"\n[3/4] Running {len(queries)} queries...")

    successful = 0
    for q in queries:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=q["query"],
            memory="Auto",
            stream=False
        )
        response_text = response.content.lower() if hasattr(response, 'content') else ""
        if any(kw.lower() in response_text for kw in q["expected_keywords"]):
            successful += 1
            print(f"      ✓ [{q['category']}] {q['query'][:35]}...")
        else:
            print(f"      ✗ [{q['category']}] {q['query'][:35]}...")

    duration = time.time() - start
    success_rate = successful / len(queries) * 100

    global_metrics.record_test("Full Scale (80 docs)", {
        "documents": len(docs),
        "queries": len(queries),
        "successful": successful,
        "duration": duration
    })

    print(f"\n[4/4] Results:")
    print(f"      Success rate: {success_rate:.1f}%")
    print(f"      Duration: {duration:.2f}s")


@pytest.mark.asyncio
async def test_sqlite_codebase_integration(global_metrics):
    """
    Test SQLite codebase retrieval.
    """
    from pathlib import Path
    from tests.test_sqlite_codebase import (
        get_sqlite_files,
        get_code_test_queries,
        SQLITE_PATH
    )

    print(f"\n{'='*60}")
    print("CODEBASE TEST: SQLite Source Code")
    print(f"{'='*60}\n")

    if not SQLITE_PATH.exists():
        print("      Skipping - SQLite source not found")
        global_metrics.record_test("SQLite Codebase", {
            "documents": 0,
            "queries": 0,
            "successful": 0,
            "duration": 0
        })
        return

    client = get_client()
    start = time.time()

    # Get files
    files = get_sqlite_files(max_files=20)
    print(f"Testing with {len(files)} SQLite files\n")

    # Create assistant
    print("[1/4] Creating assistant...")
    assistant = await client.create_assistant(
        name="sqlite-integration-test",
        description="SQLite codebase test"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Upload files
    print(f"[2/4] Uploading {len(files)} files...")
    for filename, category, content in files:
        file_content = f"## SQLite {category}: {filename}\n\n```\n{content[:5000]}\n```"
        await client.add_message(
            thread_id=thread.thread_id,
            content=file_content,
            memory="Auto",
            stream=False
        )
        print(f"      ✓ {filename}")

    print("      Waiting for indexing...")
    await asyncio.sleep(5)

    # Run queries
    queries = get_code_test_queries()[:8]
    print(f"\n[3/4] Running {len(queries)} code queries...")

    successful = 0
    for q in queries:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=q["query"],
            memory="Auto",
            stream=False
        )
        response_text = response.content.lower() if hasattr(response, 'content') else ""
        if any(kw.lower() in response_text for kw in q["expected_keywords"]):
            successful += 1
            print(f"      ✓ [{q['category']}] {q['query'][:35]}...")
        else:
            print(f"      ✗ [{q['category']}] {q['query'][:35]}...")

    duration = time.time() - start
    success_rate = successful / len(queries) * 100 if queries else 0

    global_metrics.record_test("SQLite Codebase", {
        "documents": len(files),
        "queries": len(queries),
        "successful": successful,
        "duration": duration
    })

    print(f"\n[4/4] Results:")
    print(f"      Success rate: {success_rate:.1f}%")
    print(f"      Duration: {duration:.2f}s")


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "-s"])
