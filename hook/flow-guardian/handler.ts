/**
 * Flow Guardian Hook Handler
 *
 * Automatically manages session context persistence:
 * - On bootstrap: injects previous handoff state + learnings + git context
 * - On stop/reset/new: reminds agent to save handoff
 */

import { execSync } from "child_process";
import { readFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

// Resolve paths
const HOME = process.env.HOME || process.env.USERPROFILE || "~";
const SKILL_DIR = join(HOME, ".openclaw/skills/flow-guardian");
const WORKSPACE =
  process.env.OPENCLAW_WORKSPACE ||
  process.env.WORKSPACE ||
  join(HOME, ".openclaw/workspace");
const MEMORY_DIR = join(WORKSPACE, "memory");
const HANDOFF_PATH = join(MEMORY_DIR, "handoff.yaml");
const LEARNINGS_PATH = join(MEMORY_DIR, "learnings.md");

// Config from environment
const AUTO_INJECT = process.env.FLOW_GUARDIAN_AUTO_INJECT !== "false";
const AUTO_CAPTURE = process.env.FLOW_GUARDIAN_AUTO_CAPTURE !== "false";

function ensureMemoryDir(): void {
  if (!existsSync(MEMORY_DIR)) {
    mkdirSync(MEMORY_DIR, { recursive: true });
  }
}

function loadHandoff(): string | null {
  if (!existsSync(HANDOFF_PATH)) return null;
  try {
    const content = readFileSync(HANDOFF_PATH, "utf-8").trim();
    return content || null;
  } catch {
    return null;
  }
}

function getRecentLearnings(limit: number = 5): string | null {
  if (!existsSync(LEARNINGS_PATH)) return null;
  try {
    const content = readFileSync(LEARNINGS_PATH, "utf-8");
    const lines = content
      .split("\n")
      .filter((l) => l.startsWith("- "));
    if (lines.length === 0) return null;
    return lines.slice(-limit).join("\n");
  } catch {
    return null;
  }
}

function captureGitState(): string | null {
  try {
    const scriptPath = join(SKILL_DIR, "git_capture.py");
    if (!existsSync(scriptPath)) return null;
    const result = execSync(`python3 "${scriptPath}" --compact`, {
      timeout: 5000,
      encoding: "utf-8",
      cwd: WORKSPACE,
    });
    return result.trim() || null;
  } catch {
    return null;
  }
}

// Hook event interface (minimal, compatible with OpenClaw hook system)
interface HookEvent {
  action: string;
  [key: string]: unknown;
}

export default async function handler(event: HookEvent): Promise<void> {
  ensureMemoryDir();

  // --- Session Start: Inject Context ---
  if (event.action === "bootstrap" && AUTO_INJECT) {
    const parts: string[] = [];

    const handoff = loadHandoff();
    if (handoff) {
      parts.push("## Previous Session State");
      parts.push(handoff);
    }

    const learnings = getRecentLearnings();
    if (learnings) {
      parts.push("\n## Recent Learnings");
      parts.push(learnings);
    }

    const git = captureGitState();
    if (git) {
      parts.push("\n## Current Git State");
      parts.push(git);
    }

    if (parts.length > 0) {
      console.log("[flow-guardian] Injecting session context:");
      console.log(parts.join("\n"));
    } else {
      console.log("[flow-guardian] No previous session context found.");
    }
  }

  // --- Session End: Remind to Capture State ---
  if (
    ["stop", "reset", "new"].includes(event.action) &&
    AUTO_CAPTURE
  ) {
    console.log(
      "[flow-guardian] Session ending. Consider saving handoff state with:"
    );
    console.log(
      `  python3 "${join(SKILL_DIR, "handoff.py")}" save --goal "..." --now "..." --status in_progress`
    );
  }
}
