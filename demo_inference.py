#!/usr/bin/env python3
"""
Cerebras + Backboard Fast Inference Demo
- Ultra-fast LLM inference with Cerebras (3000+ tokens/sec)
- Persistent semantic memory with Backboard
- Load local codebase files as context
- Interactive CLI query loop
"""

import asyncio
import os
import time
import glob
from pathlib import Path
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
from backboard import BackboardClient

load_dotenv()


class FastInferenceLayer:
    """Combines Cerebras fast inference with Backboard semantic memory."""

    def __init__(self):
        self.cerebras = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
        self.backboard = BackboardClient(api_key=os.environ["BACKBOARD_API_KEY"])
        self.assistant_id = None
        self.thread_id = None
        # Local context cache for immediate retrieval while Backboard indexes
        self.context_cache: list[str] = []

    async def setup(self, name: str, description: str):
        """Create assistant and thread."""
        assistant = await self.backboard.create_assistant(
            name=name,
            description=description
        )
        self.assistant_id = assistant.assistant_id
        thread = await self.backboard.create_thread(self.assistant_id)
        self.thread_id = thread.thread_id
        return assistant.assistant_id

    async def load_codebase(self, directory: str, patterns: list[str] = None):
        """Load local codebase files into Backboard memory."""
        if patterns is None:
            patterns = ["*.py"]

        files_loaded = 0
        for pattern in patterns:
            for filepath in glob.glob(os.path.join(directory, "**", pattern), recursive=True):
                # Skip __pycache__ and hidden directories
                if "__pycache__" in filepath or "/." in filepath:
                    continue

                try:
                    with open(filepath, "r") as f:
                        content = f.read()

                    # Skip empty files
                    if not content.strip():
                        continue

                    # Store file with metadata
                    rel_path = os.path.relpath(filepath, directory)
                    file_context = f"## File: {rel_path}\n```python\n{content}\n```"

                    await self.backboard.add_message(
                        thread_id=self.thread_id,
                        content=file_context,
                        memory="Auto",
                        stream=False
                    )
                    # Also cache locally for immediate availability
                    self.context_cache.append(file_context)
                    files_loaded += 1
                    print(f"  Loaded: {rel_path}")
                except Exception as e:
                    print(f"  Skip: {filepath} ({e})")

        return files_loaded

    async def query(self, question: str) -> tuple[str, float, int]:
        """Query with context retrieval + Cerebras inference."""
        start = time.time()

        # 1. Try to retrieve from Backboard memory
        memories = []
        try:
            recall = await self.backboard.add_message(
                thread_id=self.thread_id,
                content=question,
                memory="Auto",
                stream=False
            )
            if hasattr(recall, "retrieved_memories") and recall.retrieved_memories:
                memories = recall.retrieved_memories
        except Exception:
            pass  # Fall back to local cache

        # 2. Build prompt with context (Backboard memories or local cache)
        if memories:
            context_str = "\n---\n".join([m.memory for m in memories])
            source = "backboard"
        elif self.context_cache:
            # Use local cache - take first few files to fit context
            context_str = "\n---\n".join(self.context_cache[:5])
            source = "local"
        else:
            context_str = "No context available."
            source = "none"

        prompt = f"""You are a helpful code assistant. Answer based on the context provided.

Context from codebase:
{context_str}

Question: {question}

Answer concisely:"""

        # 3. Fast inference with Cerebras (Llama 3.3 70B)
        response = self.cerebras.chat.completions.create(
            model="llama-3.3-70b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )

        elapsed = time.time() - start
        num_ctx = len(memories) if memories else len(self.context_cache[:5])
        return response.choices[0].message.content, elapsed, num_ctx


async def main():
    print("=" * 60)
    print("  Cerebras + Backboard Fast Inference Demo")
    print("=" * 60)

    # Check environment variables
    if not os.environ.get("CEREBRAS_API_KEY"):
        print("ERROR: CEREBRAS_API_KEY not set")
        return
    if not os.environ.get("BACKBOARD_API_KEY"):
        print("ERROR: BACKBOARD_API_KEY not set")
        return

    layer = FastInferenceLayer()

    # Setup assistant
    print("\n[1] Setting up assistant...")
    assistant_id = await layer.setup(
        name="codebase-assistant",
        description="Expert code assistant with access to the loaded codebase."
    )
    print(f"    Assistant ID: {assistant_id}")

    # Load codebase
    codebase_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\n[2] Loading codebase from: {codebase_dir}")
    files_loaded = await layer.load_codebase(codebase_dir, ["*.py"])
    print(f"    Loaded {files_loaded} files into memory")

    # Wait for indexing
    print("\n[3] Waiting for memory indexing...")
    await asyncio.sleep(3)

    # Interactive query loop
    print("\n[4] Interactive Query Mode (type 'quit' to exit)")
    print("-" * 60)

    while True:
        try:
            question = input("\n> Your question: ").strip()
            if question.lower() in ["quit", "exit", "q"]:
                break
            if not question:
                continue

            print("  Thinking...")
            response, elapsed, num_memories = await layer.query(question)

            print(f"\n  Response ({elapsed:.2f}s, {num_memories} memories retrieved):")
            print("-" * 40)
            print(response)
            print("-" * 40)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  Error: {e}")

    print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
