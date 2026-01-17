'use client';

import { useCallback, useEffect, useState, useMemo } from 'react';
import {
  ReactFlow,
  type Node,
  type Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  type NodeTypes,
  Handle,
  Position,
  Panel,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';
import { GitBranch, Lightbulb, Hash, AlertCircle, Sparkles, Filter, ZoomIn, ZoomOut, Maximize2, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Node type colors - matching Cyber Aurora theme
const NODE_COLORS = {
  session: {
    bg: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    border: '#818cf8',
    glow: 'rgba(99, 102, 241, 0.5)',
    icon: '#c7d2fe'
  },
  learning: {
    bg: 'linear-gradient(135deg, #06b6d4 0%, #10b981 100%)',
    border: '#34d399',
    glow: 'rgba(16, 185, 129, 0.5)',
    icon: '#a7f3d0'
  },
  tag: {
    bg: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
    border: '#c084fc',
    glow: 'rgba(168, 85, 247, 0.5)',
    icon: '#e9d5ff'
  },
  issue: {
    bg: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
    border: '#fbbf24',
    glow: 'rgba(245, 158, 11, 0.5)',
    icon: '#fef3c7'
  },
};

// Custom node component with glow effect
function CustomNode({ data, type }: { data: any; type: string }) {
  const colors = NODE_COLORS[type as keyof typeof NODE_COLORS] || NODE_COLORS.learning;

  const getIcon = () => {
    switch (type) {
      case 'session':
        return <GitBranch className="w-3.5 h-3.5" style={{ color: colors.icon }} />;
      case 'learning':
        return <Lightbulb className="w-3.5 h-3.5" style={{ color: colors.icon }} />;
      case 'tag':
        return <Hash className="w-3.5 h-3.5" style={{ color: colors.icon }} />;
      case 'issue':
        return <AlertCircle className="w-3.5 h-3.5" style={{ color: colors.icon }} />;
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="group relative"
    >
      {/* Glow effect */}
      <div
        className="absolute -inset-2 rounded-2xl opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-300"
        style={{ background: colors.glow }}
      />

      {/* Node card */}
      <div
        className="relative px-4 py-3 rounded-xl shadow-2xl border min-w-[140px] max-w-[220px] cursor-pointer transition-all duration-200 hover:scale-105"
        style={{
          background: colors.bg,
          borderColor: colors.border,
          boxShadow: `0 4px 20px ${colors.glow}`,
        }}
      >
        <Handle
          type="target"
          position={Position.Top}
          className="!w-3 !h-3 !border-2 !border-white/40 !bg-white/20 !-top-1.5"
        />

        {/* Header with icon and type */}
        <div className="flex items-center gap-2 mb-1.5">
          <div className="p-1 rounded-md bg-white/10">
            {getIcon()}
          </div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-white/70">
            {type}
          </span>
        </div>

        {/* Label */}
        <div className="text-sm font-medium text-white truncate leading-tight">
          {data.label}
        </div>

        {/* Subtitle based on type */}
        {type === 'session' && data.branch && (
          <div className="text-[11px] text-white/60 mt-1 truncate font-mono">
            {data.branch}
          </div>
        )}
        {type === 'learning' && data.tags?.length > 0 && (
          <div className="flex gap-1 mt-1.5 flex-wrap">
            {data.tags.slice(0, 2).map((t: string) => (
              <span
                key={t}
                className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/15 text-white/80"
              >
                #{t}
              </span>
            ))}
            {data.tags.length > 2 && (
              <span className="text-[9px] text-white/50">+{data.tags.length - 2}</span>
            )}
          </div>
        )}

        <Handle
          type="source"
          position={Position.Bottom}
          className="!w-3 !h-3 !border-2 !border-white/40 !bg-white/20 !-bottom-1.5"
        />
      </div>
    </motion.div>
  );
}

// Node types for React Flow
const nodeTypes: NodeTypes = {
  session: (props: any) => <CustomNode {...props} type="session" />,
  learning: (props: any) => <CustomNode {...props} type="learning" />,
  tag: (props: any) => <CustomNode {...props} type="tag" />,
  issue: (props: any) => <CustomNode {...props} type="issue" />,
};

interface GraphData {
  nodes: Array<{
    id: string;
    type: string;
    label: string;
    data: any;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    label?: string;
  }>;
  stats: {
    total_nodes: number;
    total_edges: number;
    sessions: number;
    learnings: number;
    tags: number;
  };
}

interface KnowledgeGraphProps {
  onNodeSelect?: (node: Node | null) => void;
}

// Improved layout algorithm - spiral with type clustering
function calculateNodePositions(nodes: GraphData['nodes'], centerX: number, centerY: number) {
  const typeGroups: Record<string, typeof nodes> = {
    tag: [],
    session: [],
    learning: [],
    issue: [],
  };

  // Group nodes by type
  nodes.forEach(node => {
    if (typeGroups[node.type]) {
      typeGroups[node.type].push(node);
    } else {
      typeGroups.learning.push(node);
    }
  });

  const positions: Record<string, { x: number; y: number }> = {};

  // Tags in the center ring
  const tagRadius = 150;
  typeGroups.tag.forEach((node, i) => {
    const angle = (i / Math.max(typeGroups.tag.length, 1)) * 2 * Math.PI - Math.PI / 2;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * tagRadius,
      y: centerY + Math.sin(angle) * tagRadius,
    };
  });

  // Sessions in the outer ring
  const sessionRadius = 450;
  typeGroups.session.forEach((node, i) => {
    const angle = (i / Math.max(typeGroups.session.length, 1)) * 2 * Math.PI - Math.PI / 2;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * sessionRadius,
      y: centerY + Math.sin(angle) * sessionRadius,
    };
  });

  // Learnings spread in a grid-like pattern between tags and sessions
  const learningNodes = typeGroups.learning;
  const cols = Math.ceil(Math.sqrt(learningNodes.length));
  const spacing = 200;
  const gridStartX = centerX - (cols * spacing) / 2;
  const gridStartY = centerY - (cols * spacing) / 2;

  learningNodes.forEach((node, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    // Add some randomness to avoid perfect grid
    const jitterX = (Math.random() - 0.5) * 60;
    const jitterY = (Math.random() - 0.5) * 60;
    positions[node.id] = {
      x: gridStartX + col * spacing + jitterX + 300,
      y: gridStartY + row * spacing + jitterY + 200,
    };
  });

  // Issues scattered around
  typeGroups.issue.forEach((node, i) => {
    const angle = (i / Math.max(typeGroups.issue.length, 1)) * 2 * Math.PI;
    const radius = 350 + Math.random() * 100;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    };
  });

  return positions;
}

function GraphContent({ onNodeSelect }: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<GraphData['stats'] | null>(null);
  const [allData, setAllData] = useState<GraphData | null>(null);

  // Filter states
  const [showSessions, setShowSessions] = useState(true);
  const [showLearnings, setShowLearnings] = useState(true);
  const [showTags, setShowTags] = useState(true);

  const { fitView, zoomIn, zoomOut } = useReactFlow();

  // Fetch graph data
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true);
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        // Reduced limit for cleaner view
        const response = await fetch(`${apiUrl}/graph?limit=50`);

        if (!response.ok) {
          throw new Error(`Failed to fetch graph: ${response.statusText}`);
        }

        const data: GraphData = await response.json();
        setAllData(data);
        setStats(data.stats);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load graph');
        console.error('Graph fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, []);

  // Apply filters and layout
  useEffect(() => {
    if (!allData) return;

    // Filter nodes based on visibility
    const filteredNodes = allData.nodes.filter(node => {
      if (node.type === 'session' && !showSessions) return false;
      if (node.type === 'learning' && !showLearnings) return false;
      if (node.type === 'tag' && !showTags) return false;
      return true;
    });

    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));

    // Filter edges to only show connections between visible nodes
    const filteredEdges = allData.edges.filter(edge =>
      visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );

    // Calculate positions with improved layout
    const positions = calculateNodePositions(filteredNodes, 600, 500);

    // Convert to React Flow format
    const flowNodes: Node[] = filteredNodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: positions[node.id] || { x: 600, y: 500 },
      data: {
        label: node.label,
        ...node.data,
      },
    }));

    const flowEdges: Edge[] = filteredEdges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.type === 'related',
      style: {
        stroke: edge.type === 'tagged'
          ? 'rgba(168, 85, 247, 0.4)'
          : 'rgba(148, 163, 184, 0.2)',
        strokeWidth: 1.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.type === 'tagged'
          ? 'rgba(168, 85, 247, 0.4)'
          : 'rgba(148, 163, 184, 0.3)',
        width: 12,
        height: 12,
      },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);

    // Fit view after layout update
    setTimeout(() => fitView({ padding: 0.2, duration: 500 }), 100);
  }, [allData, showSessions, showLearnings, showTags, setNodes, setEdges, fitView]);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeSelect?.(node);
    },
    [onNodeSelect]
  );

  const onPaneClick = useCallback(() => {
    onNodeSelect?.(null);
  }, [onNodeSelect]);

  const handleFitView = () => {
    fitView({ padding: 0.2, duration: 500 });
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </motion.div>
          <p className="text-slate-400 font-medium">Loading knowledge graph...</p>
          <p className="text-slate-600 text-sm mt-1">Mapping your AI memory</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background">
        <div className="text-center max-w-md p-8 rounded-2xl border border-red-500/20 bg-red-500/5">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-red-400 font-medium mb-2">{error}</p>
          <p className="text-slate-500 text-sm">Make sure the backend is running on port 8090</p>
        </div>
      </div>
    );
  }

  const visibleCount = nodes.length;
  const totalCount = allData?.nodes.length || 0;

  return (
    <div className="w-full h-full relative">
      {/* Filter & Controls Panel */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="absolute top-4 left-4 z-10 space-y-3"
      >
        {/* Stats */}
        <div className="rounded-2xl p-4 border border-white/[0.08] bg-slate-900/80 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-white">Knowledge Graph</span>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                {stats?.sessions || 0}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">Sessions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                {stats?.learnings || 0}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">Learnings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                {stats?.tags || 0}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">Tags</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="rounded-2xl p-4 border border-white/[0.08] bg-slate-900/80 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-white">Filters</span>
            <Badge variant="secondary" className="ml-auto bg-slate-800 text-slate-400 text-xs">
              {visibleCount}/{totalCount}
            </Badge>
          </div>
          <div className="space-y-2">
            <FilterButton
              active={showSessions}
              onClick={() => setShowSessions(!showSessions)}
              color="from-indigo-500 to-purple-500"
              label="Sessions"
              count={stats?.sessions || 0}
            />
            <FilterButton
              active={showLearnings}
              onClick={() => setShowLearnings(!showLearnings)}
              color="from-cyan-500 to-emerald-500"
              label="Learnings"
              count={stats?.learnings || 0}
            />
            <FilterButton
              active={showTags}
              onClick={() => setShowTags(!showTags)}
              color="from-purple-500 to-pink-500"
              label="Tags"
              count={stats?.tags || 0}
            />
          </div>
        </div>
      </motion.div>

      {/* Zoom Controls */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="absolute top-4 right-4 z-10"
      >
        <div className="rounded-2xl p-2 border border-white/[0.08] bg-slate-900/80 backdrop-blur-xl flex flex-col gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => zoomIn({ duration: 300 })}
            className="h-9 w-9 text-slate-400 hover:text-white hover:bg-white/10"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => zoomOut({ duration: 300 })}
            className="h-9 w-9 text-slate-400 hover:text-white hover:bg-white/10"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <div className="h-px bg-white/10 my-1" />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleFitView}
            className="h-9 w-9 text-slate-400 hover:text-white hover:bg-white/10"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </motion.div>

      {/* Interaction hint */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 text-xs text-slate-500 bg-slate-900/60 px-4 py-2 rounded-full backdrop-blur"
      >
        Click a node to see details • Drag to rearrange • Scroll to zoom
      </motion.div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(148, 163, 184, 0.05)" gap={32} size={1} />
      </ReactFlow>
    </div>
  );
}

// Filter button component
function FilterButton({
  active,
  onClick,
  color,
  label,
  count,
}: {
  active: boolean;
  onClick: () => void;
  color: string;
  label: string;
  count: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
        active
          ? 'bg-white/5 border border-white/10'
          : 'opacity-50 hover:opacity-75'
      }`}
    >
      <div className={`w-4 h-4 rounded bg-gradient-to-r ${color}`} />
      <span className="text-sm text-slate-300 flex-1 text-left">{label}</span>
      <span className="text-xs text-slate-500">{count}</span>
      {active ? (
        <Eye className="w-3.5 h-3.5 text-slate-400" />
      ) : (
        <EyeOff className="w-3.5 h-3.5 text-slate-600" />
      )}
    </button>
  );
}

// Wrapper with ReactFlowProvider
export function KnowledgeGraph({ onNodeSelect }: KnowledgeGraphProps) {
  return (
    <ReactFlowProvider>
      <GraphContent onNodeSelect={onNodeSelect} />
    </ReactFlowProvider>
  );
}
