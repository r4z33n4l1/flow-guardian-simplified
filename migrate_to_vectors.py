#!/usr/bin/env python3
"""Migration script for Flow Guardian vector store.

Migrates existing learnings and sessions from JSON storage to the
SQLite + sqlite-vec vector store for semantic search capabilities.

Usage:
    python migrate_to_vectors.py              # Migrate all data
    python migrate_to_vectors.py --dry-run    # Show what would be migrated
    python migrate_to_vectors.py --learnings  # Only migrate learnings
    python migrate_to_vectors.py --sessions   # Only migrate sessions
    python migrate_to_vectors.py --batch 50   # Process in batches of 50
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Flow Guardian storage paths
STORAGE_DIR = Path.home() / ".flow-guardian"
SESSIONS_DIR = STORAGE_DIR / "sessions"
SESSIONS_INDEX = SESSIONS_DIR / "index.json"
LEARNINGS_FILE = STORAGE_DIR / "learnings.json"


def load_learnings() -> list[dict]:
    """Load existing learnings from JSON file."""
    if not LEARNINGS_FILE.exists():
        return []
    try:
        with open(LEARNINGS_FILE) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load learnings: {e}")
        return []


def load_sessions() -> list[dict]:
    """Load existing sessions from JSON files."""
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    # Load from index first
    if SESSIONS_INDEX.exists():
        try:
            with open(SESSIONS_INDEX) as f:
                index = json.load(f)
                if isinstance(index, list):
                    for entry in index:
                        session_id = entry.get("id", "")
                        session_file = SESSIONS_DIR / f"{session_id}.json"
                        if session_file.exists():
                            try:
                                with open(session_file) as sf:
                                    session = json.load(sf)
                                    if isinstance(session, dict):
                                        sessions.append(session)
                            except (json.JSONDecodeError, IOError):
                                # Use index entry as fallback
                                sessions.append(entry)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load session index: {e}")

    return sessions


def migrate_learnings(
    store,
    embeddings_module,
    learnings: list[dict],
    batch_size: int = 32,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate learnings to vector store.

    Returns (success_count, error_count).
    """
    if not learnings:
        print("No learnings to migrate")
        return 0, 0

    success = 0
    errors = 0

    print(f"\nMigrating {len(learnings)} learnings...")

    # Process in batches for efficiency
    for i in range(0, len(learnings), batch_size):
        batch = learnings[i:i + batch_size]

        # Prepare texts for batch embedding
        texts = []
        for learning in batch:
            insight = learning.get("insight") or learning.get("text", "")
            texts.append(f"**Learning:** {insight}")

        if dry_run:
            print(f"  Would migrate batch {i//batch_size + 1}: {len(batch)} learnings")
            success += len(batch)
            continue

        # Generate embeddings in batch
        try:
            embeddings = embeddings_module.get_embeddings_batch(texts, batch_size=batch_size)
        except Exception as e:
            print(f"  Error generating embeddings for batch: {e}")
            errors += len(batch)
            continue

        # Store each learning
        for j, (learning, embedding) in enumerate(zip(batch, embeddings)):
            try:
                learning_id = learning.get("id") or f"learning_migrated_{i + j}"
                insight = learning.get("insight") or learning.get("text", "")
                tags = learning.get("tags", [])
                is_team = learning.get("team", False) or learning.get("shared", False)

                store.store(
                    content=f"**Learning:** {insight}",
                    embedding=embedding,
                    namespace="team" if is_team else "personal",
                    content_type="learning",
                    metadata={
                        "tags": tags,
                        "author": learning.get("author"),
                        "shared": is_team,
                        "timestamp": learning.get("timestamp"),
                        "migrated_at": datetime.now().isoformat(),
                    },
                    memory_id=learning_id,
                )
                success += 1
            except Exception as e:
                print(f"  Error storing learning {learning_id}: {e}")
                errors += 1

        print(f"  Batch {i//batch_size + 1}/{(len(learnings) + batch_size - 1)//batch_size}: "
              f"{success} migrated, {errors} errors")

    return success, errors


def migrate_sessions(
    store,
    embeddings_module,
    sessions: list[dict],
    batch_size: int = 32,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate sessions to vector store.

    Returns (success_count, error_count).
    """
    if not sessions:
        print("No sessions to migrate")
        return 0, 0

    success = 0
    errors = 0

    print(f"\nMigrating {len(sessions)} sessions...")

    # Process in batches
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i:i + batch_size]

        # Prepare texts for batch embedding
        texts = []
        for session in batch:
            context = session.get("context", {})
            git = session.get("git", {})
            summary = context.get("summary") or session.get("summary", "")
            branch = git.get("branch") or session.get("branch", "unknown")

            content_parts = [f"**Session:** {summary}"]
            content_parts.append(f"Branch: {branch}")
            if context.get("decisions"):
                content_parts.append(f"Decisions: {', '.join(context['decisions'])}")
            if context.get("next_steps"):
                content_parts.append(f"Next steps: {', '.join(context['next_steps'])}")
            if context.get("blockers"):
                content_parts.append(f"Blockers: {', '.join(context['blockers'])}")

            texts.append("\n".join(content_parts))

        if dry_run:
            print(f"  Would migrate batch {i//batch_size + 1}: {len(batch)} sessions")
            success += len(batch)
            continue

        # Generate embeddings in batch
        try:
            embeddings = embeddings_module.get_embeddings_batch(texts, batch_size=batch_size)
        except Exception as e:
            print(f"  Error generating embeddings for batch: {e}")
            errors += len(batch)
            continue

        # Store each session
        for j, (session, embedding, text) in enumerate(zip(batch, embeddings, texts)):
            try:
                session_id = session.get("id") or f"session_migrated_{i + j}"
                context = session.get("context", {})
                git = session.get("git", {})
                branch = git.get("branch") or session.get("branch", "unknown")

                store.store(
                    content=text,
                    embedding=embedding,
                    namespace="personal",
                    content_type="session",
                    metadata={
                        "session_id": session_id,
                        "branch": branch,
                        "files": context.get("files", []),
                        "tags": session.get("metadata", {}).get("tags", []),
                        "timestamp": session.get("timestamp"),
                        "migrated_at": datetime.now().isoformat(),
                    },
                    memory_id=session_id,
                )
                success += 1
            except Exception as e:
                print(f"  Error storing session {session_id}: {e}")
                errors += 1

        print(f"  Batch {i//batch_size + 1}/{(len(sessions) + batch_size - 1)//batch_size}: "
              f"{success} migrated, {errors} errors")

    return success, errors


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Flow Guardian data to vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually migrating"
    )
    parser.add_argument(
        "--learnings",
        action="store_true",
        help="Only migrate learnings"
    )
    parser.add_argument(
        "--sessions",
        action="store_true",
        help="Only migrate sessions"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=32,
        help="Batch size for embedding generation (default: 32)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to vector database (default: ~/.flow-guardian/vectors.db)"
    )

    args = parser.parse_args()

    # If neither --learnings nor --sessions specified, do both
    migrate_all = not args.learnings and not args.sessions

    print("Flow Guardian Vector Store Migration")
    print("=" * 40)
    print(f"Storage directory: {STORAGE_DIR}")
    print(f"Dry run: {args.dry_run}")
    print(f"Batch size: {args.batch}")

    # Load existing data
    learnings = load_learnings() if migrate_all or args.learnings else []
    sessions = load_sessions() if migrate_all or args.sessions else []

    print(f"\nFound:")
    print(f"  - {len(learnings)} learnings")
    print(f"  - {len(sessions)} sessions")

    if not learnings and not sessions:
        print("\nNo data to migrate!")
        return 0

    # Import vector storage modules
    if not args.dry_run:
        try:
            import embeddings
            if not embeddings.is_available():
                print("\nError: Embedding model not available.")
                print("Install with: pip install sentence-transformers torch")
                return 1
            print(f"\nEmbedding model: {embeddings.get_model_info()['model_name']}")
        except ImportError as e:
            print(f"\nError: Could not import embeddings module: {e}")
            print("Make sure embeddings.py is in the same directory.")
            return 1

        try:
            import vector_storage
            store = vector_storage.VectorStore(args.db_path) if args.db_path else vector_storage.get_store()
            print(f"Vector database: {store.db_path}")
        except ImportError as e:
            print(f"\nError: Could not import vector_storage module: {e}")
            return 1
    else:
        embeddings = None
        store = None

    # Perform migration
    total_success = 0
    total_errors = 0

    if learnings:
        success, errors = migrate_learnings(
            store, embeddings, learnings,
            batch_size=args.batch, dry_run=args.dry_run
        )
        total_success += success
        total_errors += errors

    if sessions:
        success, errors = migrate_sessions(
            store, embeddings, sessions,
            batch_size=args.batch, dry_run=args.dry_run
        )
        total_success += success
        total_errors += errors

    # Summary
    print("\n" + "=" * 40)
    print("Migration Summary:")
    print(f"  Successfully migrated: {total_success}")
    print(f"  Errors: {total_errors}")

    if not args.dry_run and store:
        stats = store.get_stats()
        print(f"\nVector store stats:")
        print(f"  Total memories: {stats['total']}")
        print(f"  By namespace: {stats['by_namespace']}")
        print(f"  By type: {stats['by_content_type']}")

    if args.dry_run:
        print("\nThis was a dry run. No data was actually migrated.")
        print("Run without --dry-run to perform the migration.")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
