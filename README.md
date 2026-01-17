# Flow Guardian

**"Claude forgets. Flow Guardian remembers."**

Persistent memory for AI coding sessions. Save your context, learnings, and decisions — restore them in future sessions.

Built for the [8090 x Highline Beta: Build for Builders Hackathon](https://lu.ma/8090-hackathon).

## The Problem

1. You have a great coding session with Claude
2. You figure out how your codebase works, debug issues, make decisions
3. Session ends or context fills up
4. **Claude has amnesia.** You explain the same things. Again.

## The Solution

```bash
flow save       # Checkpoint your session
flow resume     # Restore context in new session
flow learn      # Store insights that persist forever
flow recall     # Search everything you've learned
flow team       # Search team's shared knowledge
```

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Use
flow save -m "Before standup"
flow resume
```

## Tech Stack

- **Cerebras** — Fast inference for context analysis
- **Backboard.io** — Persistent memory with semantic recall
- **Rich** — Beautiful CLI output

## Documentation

See `specs/` for detailed feature specifications.

## License

MIT
