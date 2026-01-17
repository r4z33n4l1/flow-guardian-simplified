"use client";

import { useCallback, useEffect, useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Keyboard, Pagination, Navigation } from "swiper/modules";
import type { Swiper as SwiperType } from "swiper";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Server,
  Database,
  MessageSquare,
  GitBranch,
  Zap,
  Terminal,
  Layout,
  CheckCircle,
  ArrowRight,
  Cloud,
  Cpu,
  FileText,
  ChevronLeft,
  ChevronRight,
  Home
} from "lucide-react";
import Link from "next/link";

import "swiper/css";
import "swiper/css/pagination";
import "swiper/css/navigation";

// Theme colors
const theme = {
  bg: "bg-[#FAF8F5]", // warm beige
  bgAlt: "bg-[#F5F0E8]", // slightly darker beige
  card: "bg-white",
  cardBorder: "border-[#E8E0D4]",
  text: "text-[#2D2A26]", // dark brown
  textMuted: "text-[#6B6560]", // muted brown
  accent: "text-orange-500",
  accentBg: "bg-orange-500",
  accentLight: "bg-orange-50",
  accentBorder: "border-orange-200",
};

// Slide wrapper component
function Slide({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`h-full w-full flex flex-col items-center justify-center p-8 md:p-16 ${theme.bg} ${className}`}>
      {children}
    </div>
  );
}

// Animated box component for diagrams
function AnimatedBox({
  children,
  delay = 0,
  className = "",
  onClick
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className={className}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}

// Animated arrow
function AnimatedArrow({ delay = 0, direction = "right" }: { delay?: number; direction?: "right" | "down" }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.3 }}
      className="text-orange-400"
    >
      {direction === "right" ? (
        <ArrowRight className="w-6 h-6" />
      ) : (
        <ArrowRight className="w-6 h-6 rotate-90" />
      )}
    </motion.div>
  );
}

// Title Slide
function TitleSlide() {
  return (
    <Slide>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="text-center"
      >
        <div className="flex items-center justify-center gap-4 mb-8">
          <Brain className="w-16 h-16 md:w-20 md:h-20 text-orange-500" />
        </div>
        <h1 className={`text-4xl md:text-6xl font-bold ${theme.text} mb-4`}>
          Flow Guardian
        </h1>
        <p className={`text-xl md:text-2xl ${theme.textMuted} mb-6`}>
          AI Team Memory System
        </p>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-lg text-orange-500"
        >
          Persistent context for AI coding assistants
        </motion.p>
      </motion.div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className={`absolute bottom-8 ${theme.textMuted} text-sm`}
      >
        Use arrow keys or swipe to navigate
      </motion.div>
    </Slide>
  );
}

// Problem Slide
function ProblemSlide() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(s => (s < 3 ? s + 1 : s));
    }, 800);
    return () => clearInterval(timer);
  }, []);

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-12`}>The Problem</h2>

      <div className="flex flex-col md:flex-row items-center gap-6 md:gap-12">
        {/* Session 1 */}
        <AnimatedBox delay={0} className={`${theme.card} border ${theme.cardBorder} rounded-xl p-5 w-64 shadow-sm`}>
          <div className="flex items-center gap-2 mb-3">
            <Terminal className="w-4 h-4 text-orange-500" />
            <span className="text-orange-500 font-mono text-sm">Session 1</span>
          </div>
          <p className={`${theme.text} font-medium mb-2`}>Working on Auth</p>
          <ul className={`text-sm ${theme.textMuted} space-y-1`}>
            <li>Fixed JWT validation</li>
            <li>Discovered edge case</li>
            <li>Found workaround</li>
          </ul>
          {step >= 1 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-3 text-red-500 text-sm font-medium"
            >
              Session ends...
            </motion.div>
          )}
        </AnimatedBox>

        {step >= 2 && <AnimatedArrow delay={0} />}

        {/* Session 2 */}
        {step >= 2 && (
          <AnimatedBox delay={0.2} className={`${theme.card} border ${theme.cardBorder} rounded-xl p-5 w-64 shadow-sm`}>
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-orange-400" />
              <span className="text-orange-400 font-mono text-sm">Session 2</span>
            </div>
            <p className={`${theme.text} font-medium mb-2`}>Continue Auth Fixing</p>
            <ul className="text-sm text-red-400 space-y-1">
              <li>Where was I?</li>
              <li>What did I try?</li>
              <li>Same mistakes again...</li>
            </ul>
          </AnimatedBox>
        )}
      </div>

      {step >= 3 && (
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-lg text-red-500 mt-10 text-center"
        >
          Without memory, AI assistants lose valuable context
        </motion.p>
      )}
    </Slide>
  );
}

// Solution Slide
function SolutionSlide() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(s => (s < 2 ? s + 1 : s));
    }, 600);
    return () => clearInterval(timer);
  }, []);

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-12`}>The Solution</h2>

      <div className="flex flex-col md:flex-row items-center gap-6 md:gap-6">
        {/* Session 1 */}
        <AnimatedBox delay={0} className={`${theme.card} border-2 border-orange-200 rounded-xl p-5 w-56 shadow-sm`}>
          <div className="flex items-center gap-2 mb-3">
            <Terminal className="w-4 h-4 text-orange-500" />
            <span className="text-orange-500 font-mono text-sm">Session 1</span>
          </div>
          <p className={`${theme.text} font-medium text-sm`}>Working on Auth</p>
        </AnimatedBox>

        {/* Flow Guardian */}
        {step >= 1 && (
          <>
            <AnimatedArrow delay={0} />
            <AnimatedBox delay={0.2} className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-5 w-40 text-center shadow-lg">
              <Brain className="w-10 h-10 text-white mx-auto mb-2" />
              <p className="text-white font-bold text-sm">Flow Guardian</p>
            </AnimatedBox>
            <AnimatedArrow delay={0.4} />
          </>
        )}

        {/* Session 2 */}
        {step >= 2 && (
          <AnimatedBox delay={0.6} className={`${theme.card} border-2 border-green-200 rounded-xl p-5 w-56 shadow-sm`}>
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-green-600" />
              <span className="text-green-600 font-mono text-sm">Session 2</span>
            </div>
            <p className={`${theme.text} font-medium text-sm mb-2`}>Continue Auth Fixing</p>
            <ul className="text-xs text-green-600 space-y-1">
              <li>+ Knows previous context</li>
              <li>+ Remembers decisions</li>
              <li>+ Avoids past mistakes</li>
            </ul>
          </AnimatedBox>
        )}
      </div>

      {step >= 2 && (
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-lg text-green-600 mt-10 text-center"
        >
          Fresh context WITHOUT going through same mistakes again
        </motion.p>
      )}
    </Slide>
  );
}

// Architecture Slide
function ArchitectureSlide() {
  const [activeComponent, setActiveComponent] = useState<string | null>(null);

  const components = [
    { id: "cerebras", label: "Cerebras", icon: Cpu, desc: "LLM (Llama 3.3 70B)" },
    { id: "backboard", label: "Backboard", icon: Cloud, desc: "Cloud Memory" },
    { id: "linear", label: "Linear", icon: CheckCircle, desc: "PM Dashboard" },
    { id: "local", label: "Local Storage", icon: Database, desc: "~/.flow-guardian/" },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-8`}>System Architecture</h2>

      <div className="flex flex-col items-center gap-6">
        {/* Main Server */}
        <AnimatedBox delay={0} className="relative">
          <div
            className={`bg-orange-50 border-2 border-orange-300 rounded-xl p-5 cursor-pointer transition-all ${activeComponent === "server" ? "scale-105 bg-orange-100" : "hover:bg-orange-100"}`}
            onClick={() => setActiveComponent(activeComponent === "server" ? null : "server")}
          >
            <div className="flex items-center gap-3">
              <Server className="w-6 h-6 text-orange-500" />
              <div>
                <p className={`${theme.text} font-bold`}>Main Server</p>
                <p className="text-orange-600 text-sm">Port 8090</p>
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              <span className="px-2 py-1 bg-orange-200 rounded-full text-xs text-orange-700">API</span>
              <span className="px-2 py-1 bg-orange-200 rounded-full text-xs text-orange-700">Daemon</span>
              <span className="px-2 py-1 bg-orange-200 rounded-full text-xs text-orange-700">MCP</span>
            </div>
          </div>
        </AnimatedBox>

        {/* Arrows */}
        <div className="flex gap-12">
          <AnimatedArrow delay={0.2} direction="down" />
          <AnimatedArrow delay={0.3} direction="down" />
          <AnimatedArrow delay={0.4} direction="down" />
        </div>

        {/* External Services */}
        <div className="flex flex-wrap justify-center gap-3">
          {components.map((comp, i) => (
            <AnimatedBox key={comp.id} delay={0.3 + i * 0.1}>
              <div
                className={`${theme.card} border ${theme.cardBorder} rounded-xl p-4 cursor-pointer transition-all hover:border-orange-300 hover:shadow-md ${activeComponent === comp.id ? "border-orange-400 shadow-md" : ""}`}
                onClick={() => setActiveComponent(activeComponent === comp.id ? null : comp.id)}
              >
                <comp.icon className="w-5 h-5 text-orange-500 mb-2" />
                <p className={`${theme.text} font-medium text-sm`}>{comp.label}</p>
                <p className={`${theme.textMuted} text-xs`}>{comp.desc}</p>
              </div>
            </AnimatedBox>
          ))}
        </div>

        {/* Description */}
        <AnimatePresence mode="wait">
          {activeComponent && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`${theme.card} border ${theme.cardBorder} rounded-lg p-4 max-w-md text-center shadow-sm`}
            >
              <p className={`${theme.textMuted} text-sm`}>
                {activeComponent === "server" && "Unified Python backend with FastAPI. Runs as API server, background daemon, or MCP server for Claude Code."}
                {activeComponent === "cerebras" && "Fast LLM inference using Llama 3.3 70B. Analyzes sessions, extracts insights, generates responses."}
                {activeComponent === "backboard" && "Cloud-based semantic memory with team sharing. Enables cross-session recall and collaboration."}
                {activeComponent === "linear" && "Auto-creates issues from blockers and bugs. Generates FAQ and weekly summary docs."}
                {activeComponent === "local" && "JSON-based local storage. Fast fallback when cloud is unavailable."}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Slide>
  );
}

// Daemon Mode Slide
function DaemonSlide() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(s => (s < 4 ? s + 1 : s));
    }, 700);
    return () => clearInterval(timer);
  }, []);

  const steps = [
    { icon: FileText, title: "Watch Sessions", desc: "~/.claude/projects/", color: "orange" },
    { icon: Terminal, title: "Parse Conversation", desc: "Extract messages & code", color: "orange" },
    { icon: Cpu, title: "Analyze with LLM", desc: "Extract learnings & decisions", color: "orange" },
    { icon: Database, title: "Store & Sync", desc: "Local + Cloud + Linear", color: "orange" },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-6`}>Daemon Mode</h2>
      <p className={`${theme.textMuted} mb-8`}>Automatic context extraction from Claude Code sessions</p>

      <div className="flex flex-col gap-3 max-w-lg">
        {steps.map((s, i) => (
          step >= i && (
            <div key={i}>
              <AnimatedBox delay={0} className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0">
                  <s.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className={`${theme.text} font-medium`}>{s.title}</p>
                  <p className={`${theme.textMuted} text-sm`}>{s.desc}</p>
                </div>
              </AnimatedBox>
              {i < 3 && step > i && (
                <div className="ml-5 my-1">
                  <AnimatedArrow delay={0} direction="down" />
                </div>
              )}
            </div>
          )
        ))}
      </div>

      {step >= 4 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={`mt-6 ${theme.card} border ${theme.cardBorder} rounded-lg p-3 font-mono text-sm`}
        >
          <span className={theme.textMuted}>$</span> <span className="text-orange-500">python server.py daemon</span>
        </motion.div>
      )}
    </Slide>
  );
}

// Two-Phase Retrieval Slide
function RetrievalSlide() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setPhase(p => (p < 3 ? p + 1 : p));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-4`}>Two-Phase Retrieval</h2>
      <p className={`${theme.textMuted} mb-8`}>Local-first, cloud when needed</p>

      <div className="flex flex-col gap-4 max-w-xl w-full">
        {/* Query */}
        <AnimatedBox delay={0} className="flex items-center justify-center">
          <div className={`${theme.card} border ${theme.cardBorder} rounded-lg px-5 py-2 shadow-sm`}>
            <span className={theme.textMuted}>Query:</span>
            <span className={`${theme.text} ml-2`}>&quot;How did we handle auth?&quot;</span>
          </div>
        </AnimatedBox>

        {phase >= 1 && <AnimatedArrow delay={0} direction="down" />}

        {/* Phase 1 */}
        {phase >= 1 && (
          <AnimatedBox delay={0.1} className="bg-orange-50 border border-orange-200 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-4 h-4 text-orange-500" />
              <span className="text-orange-600 font-bold text-sm">Phase 1: Local Search</span>
              <span className="text-green-600 text-xs ml-auto">~instant</span>
            </div>
            <p className={`${theme.textMuted} text-sm`}>Search local learnings + sessions</p>
          </AnimatedBox>
        )}

        {/* Decision Point */}
        {phase >= 2 && (
          <AnimatedBox delay={0.1} className="flex items-center justify-center">
            <div className={`${theme.card} border ${theme.cardBorder} rounded-lg px-4 py-2`}>
              <span className={`${theme.textMuted} text-sm`}>Score &gt;= 3? Skip cloud</span>
            </div>
          </AnimatedBox>
        )}

        {phase >= 2 && <AnimatedArrow delay={0.2} direction="down" />}

        {/* Phase 2 */}
        {phase >= 3 && (
          <AnimatedBox delay={0.1} className="bg-orange-50 border border-orange-200 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-2">
              <Cloud className="w-4 h-4 text-orange-500" />
              <span className="text-orange-600 font-bold text-sm">Phase 2: Cloud Fetch</span>
              <span className="text-orange-500 text-xs ml-auto">~5-10s</span>
            </div>
            <p className={`${theme.textMuted} text-sm`}>Fetch from Backboard + Linear documents</p>
          </AnimatedBox>
        )}
      </div>
    </Slide>
  );
}

// MCP Tools Slide
function MCPToolsSlide() {
  const tools = [
    { name: "flow_recall", desc: "Search memory", example: 'flow_recall(query="...")' },
    { name: "flow_capture", desc: "Save context", example: 'flow_capture(summary="...")' },
    { name: "flow_learn", desc: "Store insights", example: 'flow_learn(insight="...")' },
    { name: "flow_team", desc: "Team knowledge", example: 'flow_team(query="...")' },
    { name: "flow_status", desc: "System status", example: 'flow_status()' },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-4`}>MCP Tools</h2>
      <p className={`${theme.textMuted} mb-8`}>Integrate directly with Claude Code</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
        {tools.map((tool, i) => (
          <AnimatedBox key={tool.name} delay={i * 0.1}>
            <div className={`${theme.card} border ${theme.cardBorder} rounded-lg p-4 hover:border-orange-300 transition-colors`}>
              <div className="flex items-center gap-2 mb-1">
                <Terminal className="w-4 h-4 text-orange-500" />
                <span className="text-orange-600 font-mono font-bold text-sm">{tool.name}</span>
              </div>
              <p className={`${theme.textMuted} text-sm`}>{tool.desc}</p>
            </div>
          </AnimatedBox>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className={`mt-6 ${theme.textMuted} text-sm`}
      >
        Configure in <code className="text-orange-500">.mcp.json</code>
      </motion.div>
    </Slide>
  );
}

// Web UI Slide
function WebUISlide() {
  const features = [
    { icon: MessageSquare, title: "Chat Interface", desc: "Streaming responses" },
    { icon: Zap, title: "Activity Feed", desc: "Real-time updates" },
    { icon: FileText, title: "Document Upload", desc: "PDF, TXT, MD" },
    { icon: GitBranch, title: "Knowledge Graph", desc: "Visualize connections" },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-4`}>Web UI</h2>
      <p className={`${theme.textMuted} mb-8`}>localhost:3000</p>

      <div className="grid grid-cols-2 gap-4 max-w-xl">
        {features.map((feature, i) => (
          <AnimatedBox key={feature.title} delay={i * 0.1}>
            <div className={`${theme.card} border ${theme.cardBorder} rounded-xl p-5 hover:border-orange-300 transition-colors`}>
              <feature.icon className="w-6 h-6 text-orange-500 mb-2" />
              <h3 className={`${theme.text} font-bold text-sm mb-1`}>{feature.title}</h3>
              <p className={`${theme.textMuted} text-xs`}>{feature.desc}</p>
            </div>
          </AnimatedBox>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className={`mt-6 ${theme.card} border ${theme.cardBorder} rounded-lg p-3 font-mono text-sm`}
      >
        <span className={theme.textMuted}>$</span> <span className="text-orange-500">cd flow-web && npm run dev</span>
      </motion.div>
    </Slide>
  );
}

// Linear Integration Slide
function LinearSlide() {
  const integrations = [
    { title: "Auto-Issue Creation", desc: "Blockers become issues" },
    { title: "Bug Detection", desc: "From learnings" },
    { title: "FAQ Generation", desc: "Auto-generated docs" },
    { title: "Weekly Summaries", desc: "Activity overview" },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-4`}>Linear Integration</h2>
      <p className={`${theme.textMuted} mb-8`}>Keep PM in sync with dev</p>

      <div className="flex flex-col gap-3 max-w-md">
        {integrations.map((item, i) => (
          <AnimatedBox key={item.title} delay={i * 0.1}>
            <div className={`${theme.card} border ${theme.cardBorder} rounded-lg p-4 flex items-center gap-4`}>
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <div>
                <h3 className={`${theme.text} font-medium text-sm`}>{item.title}</h3>
                <p className={`${theme.textMuted} text-xs`}>{item.desc}</p>
              </div>
            </div>
          </AnimatedBox>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className={`mt-6 flex items-center gap-2 ${theme.textMuted} text-sm`}
      >
        <CheckCircle className="w-4 h-4 text-green-500" />
        Set <code className="text-orange-500 mx-1">LINEAR_API_KEY</code> to enable
      </motion.div>
    </Slide>
  );
}

// Getting Started Slide
function GettingStartedSlide() {
  const steps = [
    { num: 1, cmd: "pip install -r requirements.txt", desc: "Install deps" },
    { num: 2, cmd: "cp .env.example .env", desc: "Configure" },
    { num: 3, cmd: "python server.py all --foreground", desc: "Start server" },
    { num: 4, cmd: "cd flow-web && npm run dev", desc: "Start UI" },
  ];

  return (
    <Slide>
      <h2 className={`text-3xl md:text-5xl font-bold ${theme.text} mb-4`}>Getting Started</h2>
      <p className={`${theme.textMuted} mb-8`}>Up and running in minutes</p>

      <div className="flex flex-col gap-3 max-w-lg">
        {steps.map((step, i) => (
          <AnimatedBox key={step.num} delay={i * 0.1}>
            <div className={`${theme.card} border ${theme.cardBorder} rounded-lg p-3 flex items-center gap-3`}>
              <div className="w-7 h-7 rounded-full bg-orange-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                {step.num}
              </div>
              <code className="text-orange-600 text-sm flex-1">{step.cmd}</code>
            </div>
          </AnimatedBox>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mt-10 text-center"
      >
        <p className={`text-xl ${theme.text} font-bold mb-2`}>Ready to build with persistent memory</p>
        <div className="flex items-center justify-center gap-2 text-orange-500">
          <Layout className="w-4 h-4" />
          <span className="text-sm">http://localhost:3000</span>
        </div>
      </motion.div>
    </Slide>
  );
}

// Main Slideshow Component
export function Slideshow() {
  const [swiper, setSwiper] = useState<SwiperType | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const totalSlides = 10;

  const handlePrev = useCallback(() => {
    swiper?.slidePrev();
  }, [swiper]);

  const handleNext = useCallback(() => {
    swiper?.slideNext();
  }, [swiper]);

  return (
    <div className={`h-screen w-screen ${theme.bg} overflow-hidden relative`}>
      {/* Navigation Header */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between">
        <Link href="/" className={`${theme.textMuted} hover:text-orange-500 transition-colors`}>
          <Home className="w-5 h-5" />
        </Link>
        <div className={`${theme.textMuted} text-sm`}>
          {currentSlide + 1} / {totalSlides}
        </div>
      </div>

      {/* Navigation Buttons */}
      <button
        onClick={handlePrev}
        className={`absolute left-4 top-1/2 -translate-y-1/2 z-20 p-2 rounded-full ${theme.card} border ${theme.cardBorder} ${theme.textMuted} hover:text-orange-500 hover:border-orange-300 transition-colors disabled:opacity-30`}
        disabled={currentSlide === 0}
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <button
        onClick={handleNext}
        className={`absolute right-4 top-1/2 -translate-y-1/2 z-20 p-2 rounded-full ${theme.card} border ${theme.cardBorder} ${theme.textMuted} hover:text-orange-500 hover:border-orange-300 transition-colors disabled:opacity-30`}
        disabled={currentSlide === totalSlides - 1}
      >
        <ChevronRight className="w-5 h-5" />
      </button>

      {/* Swiper */}
      <Swiper
        modules={[Keyboard, Pagination, Navigation]}
        keyboard={{ enabled: true }}
        pagination={{ clickable: true }}
        onSwiper={setSwiper}
        onSlideChange={(s) => setCurrentSlide(s.activeIndex)}
        className="h-full w-full"
        style={{
          // @ts-expect-error CSS custom properties
          "--swiper-pagination-color": "#f97316",
          "--swiper-pagination-bullet-inactive-color": "#d4d4d4",
        }}
      >
        <SwiperSlide><TitleSlide /></SwiperSlide>
        <SwiperSlide><ProblemSlide /></SwiperSlide>
        <SwiperSlide><SolutionSlide /></SwiperSlide>
        <SwiperSlide><ArchitectureSlide /></SwiperSlide>
        <SwiperSlide><DaemonSlide /></SwiperSlide>
        <SwiperSlide><RetrievalSlide /></SwiperSlide>
        <SwiperSlide><MCPToolsSlide /></SwiperSlide>
        <SwiperSlide><WebUISlide /></SwiperSlide>
        <SwiperSlide><LinearSlide /></SwiperSlide>
        <SwiperSlide><GettingStartedSlide /></SwiperSlide>
      </Swiper>
    </div>
  );
}
