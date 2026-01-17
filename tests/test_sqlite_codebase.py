"""
SQLite Codebase Test for Backboard.io

Tests Backboard's ability to store and recall content from a real codebase:
- C source files (.c, .h)
- Documentation (README.md, LICENSE.md, doc/ files)

Tests both code understanding and documentation retrieval.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional
import pytest
from dotenv import load_dotenv

load_dotenv()

# SQLite source path
SQLITE_PATH = Path(__file__).parent.parent / "testsql" / "sqlite"


# Skip if no API key or no SQLite source
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("BACKBOARD_API_KEY"),
        reason="BACKBOARD_API_KEY not set"
    ),
    pytest.mark.skipif(
        not SQLITE_PATH.exists(),
        reason=f"SQLite source not found at {SQLITE_PATH}"
    )
]


def get_client():
    """Create Backboard client."""
    from backboard import BackboardClient
    api_key = os.environ.get("BACKBOARD_API_KEY")
    return BackboardClient(api_key=api_key)


def get_sqlite_files(max_files: int = 30) -> List[Tuple[str, str, str]]:
    """
    Get SQLite source files for testing.

    Returns list of (filename, category, content) tuples.
    Limits content size to avoid token limits.
    """
    files = []
    max_content_size = 8000  # Limit content to ~8KB per file

    # Get key C source files
    src_path = SQLITE_PATH / "src"
    if src_path.exists():
        priority_files = [
            "sqlite3.h",  # Main header - defines API
            "main.c",     # Main entry points
            "vdbe.c",     # Virtual machine
            "btree.c",    # B-tree implementation
            "pager.c",    # Page cache
            "select.c",   # SELECT statement processing
            "insert.c",   # INSERT statement processing
            "delete.c",   # DELETE statement processing
            "update.c",   # UPDATE statement processing
            "expr.c",     # Expression evaluation
            "func.c",     # Built-in functions
            "date.c",     # Date/time functions
            "mem1.c",     # Memory allocation
            "os.c",       # OS abstraction layer
        ]

        for filename in priority_files:
            filepath = src_path / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(errors='ignore')[:max_content_size]
                    files.append((filename, "Source Code", content))
                except Exception as e:
                    print(f"Warning: Could not read {filename}: {e}")

    # Get header files
    for h_file in list(src_path.glob("*.h"))[:5]:
        if h_file.name not in [f[0] for f in files]:
            try:
                content = h_file.read_text(errors='ignore')[:max_content_size]
                files.append((h_file.name, "Header", content))
            except:
                pass

    # Get documentation files
    doc_files = [
        SQLITE_PATH / "README.md",
        SQLITE_PATH / "LICENSE.md",
    ]

    # Also check doc/ directory
    doc_dir = SQLITE_PATH / "doc"
    if doc_dir.exists():
        for doc_file in list(doc_dir.glob("*.md"))[:3]:
            doc_files.append(doc_file)

    for doc_path in doc_files:
        if doc_path.exists():
            try:
                content = doc_path.read_text(errors='ignore')[:max_content_size]
                files.append((doc_path.name, "Documentation", content))
            except Exception as e:
                print(f"Warning: Could not read {doc_path.name}: {e}")

    return files[:max_files]


def get_code_test_queries() -> List[dict]:
    """Return test queries for code understanding."""
    return [
        {
            "query": "What is the main SQLite API function for preparing SQL statements?",
            "expected_keywords": ["sqlite3_prepare", "prepare", "statement"],
            "category": "API"
        },
        {
            "query": "How does SQLite handle B-tree operations?",
            "expected_keywords": ["btree", "page", "cell", "node"],
            "category": "Implementation"
        },
        {
            "query": "What functions handle date and time in SQLite?",
            "expected_keywords": ["date", "time", "datetime", "julianday"],
            "category": "Functions"
        },
        {
            "query": "How does SQLite manage memory allocation?",
            "expected_keywords": ["malloc", "free", "memory", "alloc"],
            "category": "Memory"
        },
        {
            "query": "What is the virtual database engine (VDBE) in SQLite?",
            "expected_keywords": ["vdbe", "opcode", "virtual machine", "bytecode"],
            "category": "Implementation"
        },
        {
            "query": "How are SELECT statements processed in SQLite?",
            "expected_keywords": ["select", "query", "result", "column"],
            "category": "SQL"
        },
        {
            "query": "What license is SQLite released under?",
            "expected_keywords": ["public domain", "license", "copyright"],
            "category": "Documentation"
        },
        {
            "query": "How do I build SQLite from source?",
            "expected_keywords": ["build", "compile", "make", "configure"],
            "category": "Documentation"
        },
        {
            "query": "What are the main SQLite data types?",
            "expected_keywords": ["integer", "real", "text", "blob", "null"],
            "category": "Types"
        },
        {
            "query": "How does SQLite handle transactions?",
            "expected_keywords": ["transaction", "commit", "rollback", "begin"],
            "category": "Transactions"
        },
    ]


class SQLiteTestMetrics:
    """Collect metrics for SQLite tests."""

    def __init__(self):
        self.files_uploaded = 0
        self.upload_times: List[float] = []
        self.query_results: List[Tuple[str, bool, float]] = []
        self.total_bytes_uploaded = 0

    def report(self) -> str:
        successful = sum(1 for _, success, _ in self.query_results if success)
        avg_upload = sum(self.upload_times) / len(self.upload_times) if self.upload_times else 0
        avg_query = sum(t for _, _, t in self.query_results) / len(self.query_results) if self.query_results else 0

        return f"""
{'='*60}
SQLITE CODEBASE TEST METRICS
{'='*60}

FILES
-----
Files uploaded: {self.files_uploaded}
Total size: {self.total_bytes_uploaded / 1024:.1f} KB
Avg upload time: {avg_upload:.2f}s

QUERIES
-------
Total queries: {len(self.query_results)}
Successful: {successful}
Success rate: {(successful/len(self.query_results)*100) if self.query_results else 0:.1f}%
Avg query time: {avg_query:.2f}s

{'='*60}
"""


@pytest.mark.asyncio
async def test_sqlite_code_retrieval():
    """
    Test retrieval of SQLite source code information.
    """
    client = get_client()
    metrics = SQLiteTestMetrics()

    print(f"\n{'='*60}")
    print("SQLITE CODEBASE RETRIEVAL TEST")
    print(f"{'='*60}\n")

    # Get files to upload
    files = get_sqlite_files(max_files=25)
    if not files:
        pytest.skip("No SQLite files found to test")

    print(f"Found {len(files)} files to upload")

    # Create assistant
    print("\n[1/4] Creating assistant...")
    assistant = await client.create_assistant(
        name="sqlite-codebase-test",
        description="Test assistant for SQLite codebase analysis"
    )

    # Create thread
    print("[2/4] Creating thread...")
    thread = await client.create_thread(assistant.assistant_id)

    # Upload files
    print(f"\n[3/4] Uploading {len(files)} files...")
    for filename, category, content in files:
        start = time.time()

        # Format for upload
        file_content = f"""## SQLite {category}: {filename}

**File:** {filename}
**Category:** {category}
**Size:** {len(content)} bytes

---

```
{content[:6000]}
```
"""
        try:
            await client.add_message(
                thread_id=thread.thread_id,
                content=file_content,
                memory="Auto",
                stream=False
            )

            duration = time.time() - start
            metrics.upload_times.append(duration)
            metrics.files_uploaded += 1
            metrics.total_bytes_uploaded += len(content)

            print(f"      ✓ {filename} ({category})")

        except Exception as e:
            print(f"      ✗ {filename}: {e}")

    # Wait for indexing
    print("\n      Waiting 5 seconds for memory indexing...")
    await asyncio.sleep(5)

    # Run queries
    queries = get_code_test_queries()
    print(f"\n[4/4] Running {len(queries)} code queries...")

    for query_info in queries:
        query = query_info["query"]
        expected = query_info["expected_keywords"]

        start = time.time()
        try:
            response = await client.add_message(
                thread_id=thread.thread_id,
                content=query,
                memory="Auto",
                stream=False
            )
            duration = time.time() - start

            response_text = response.content.lower() if hasattr(response, 'content') else str(response).lower()
            found = any(kw.lower() in response_text for kw in expected)

            metrics.query_results.append((query, found, duration))

            status = "✓" if found else "✗"
            print(f"      {status} [{query_info['category']}] {query[:45]}...")

        except Exception as e:
            metrics.query_results.append((query, False, 0))
            print(f"      ✗ ERROR: {e}")

    # Print metrics
    print(metrics.report())

    # Assert success rate
    successful = sum(1 for _, success, _ in metrics.query_results if success)
    success_rate = successful / len(metrics.query_results) if metrics.query_results else 0

    assert success_rate >= 0.60, f"Success rate {success_rate:.1%} below 60% threshold"


@pytest.mark.asyncio
async def test_sqlite_specific_code_recall():
    """
    Test recall of specific code patterns from SQLite source.
    """
    client = get_client()

    print(f"\n{'='*60}")
    print("SQLITE SPECIFIC CODE RECALL TEST")
    print(f"{'='*60}\n")

    # Create assistant
    assistant = await client.create_assistant(
        name="sqlite-specific-test",
        description="Test specific code recall"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Read actual content from sqlite3.h if it exists
    header_path = SQLITE_PATH / "src" / "sqlite3.h"
    if not header_path.exists():
        # Try alternate locations
        for alt_path in [
            SQLITE_PATH / "sqlite3.h",
            SQLITE_PATH / "src" / "sqliteInt.h"
        ]:
            if alt_path.exists():
                header_path = alt_path
                break

    if header_path.exists():
        print(f"[1/3] Reading {header_path.name}...")
        content = header_path.read_text(errors='ignore')[:10000]

        print("[2/3] Uploading header file...")
        await client.add_message(
            thread_id=thread.thread_id,
            content=f"SQLite Header File ({header_path.name}):\n\n```c\n{content}\n```",
            memory="Auto",
            stream=False
        )

        await asyncio.sleep(3)

        print("[3/3] Testing specific recall...")

        # Test specific API recall
        test_apis = [
            ("sqlite3_open", "opening database"),
            ("sqlite3_close", "closing database"),
            ("SQLITE_OK", "success code"),
        ]

        for api_name, description in test_apis:
            response = await client.add_message(
                thread_id=thread.thread_id,
                content=f"What do you know about {api_name} in SQLite?",
                memory="Auto",
                stream=False
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            found = api_name.lower() in response_text.lower()

            status = "✓" if found else "✗"
            print(f"      {status} {api_name} ({description})")

    else:
        print("      Skipping - header file not found")


@pytest.mark.asyncio
async def test_sqlite_readme_retrieval():
    """
    Test retrieval of information from SQLite README.
    """
    client = get_client()

    print(f"\n{'='*60}")
    print("SQLITE README RETRIEVAL TEST")
    print(f"{'='*60}\n")

    readme_path = SQLITE_PATH / "README.md"
    if not readme_path.exists():
        pytest.skip("README.md not found")

    # Create assistant
    assistant = await client.create_assistant(
        name="sqlite-readme-test",
        description="Test README retrieval"
    )
    thread = await client.create_thread(assistant.assistant_id)

    # Upload README
    print("[1/3] Uploading README.md...")
    readme_content = readme_path.read_text(errors='ignore')

    await client.add_message(
        thread_id=thread.thread_id,
        content=f"SQLite README Documentation:\n\n{readme_content}",
        memory="Auto",
        stream=False
    )

    await asyncio.sleep(3)

    # Test queries
    print("[2/3] Testing README queries...")
    queries = [
        "What is SQLite?",
        "How do I compile SQLite?",
        "Where can I find SQLite documentation?",
    ]

    for query in queries:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=query,
            memory="Auto",
            stream=False
        )

        response_text = response.content if hasattr(response, 'content') else str(response)
        has_content = len(response_text) > 50

        status = "✓" if has_content else "✗"
        print(f"      {status} {query}")
        print(f"         Preview: {response_text[:150]}...")

    print("\n[3/3] Test complete")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_sqlite_code_retrieval())
