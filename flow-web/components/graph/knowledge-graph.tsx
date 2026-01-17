'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  type Node,
  type Edge,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  type NodeTypes,
  Handle,
  Position,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';
import { GitBranch, Lightbulb, Hash, AlertCircle, Sparkles, Filter, ZoomIn, ZoomOut, Maximize2, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Node type colors - Warm Beige + Orange theme
const NODE_COLORS = {
  session: {
    bg: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
    border: '#fb923c',
    glow: 'rgba(249, 115, 22, 0.4)',
    icon: '#ffffff'
  },
  learning: {
    bg: 'linear-gradient(135deg, #2D2A26 0%, #3d3a36 100%)',
    border: '#6B6560',
    glow: 'rgba(45, 42, 38, 0.4)',
    icon: '#FAF8F5'
  },
  tag: {
    bg: 'linear-gradient(135deg, #fb923c 0%, #f97316 100%)',
    border: '#fdba74',
    glow: 'rgba(251, 146, 60, 0.4)',
    icon: '#ffffff'
  },
  issue: {
    bg: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    border: '#f87171',
    glow: 'rgba(239, 68, 68, 0.4)',
    icon: '#ffffff'
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

// Deterministic pseudo-random based on string (for consistent layouts)
function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return (Math.abs(hash) % 1000) / 1000;
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
    // Add deterministic jitter based on node id for consistent layout
    const jitterX = (seededRandom(node.id + '_x') - 0.5) * 60;
    const jitterY = (seededRandom(node.id + '_y') - 0.5) * 60;
    positions[node.id] = {
      x: gridStartX + col * spacing + jitterX + 300,
      y: gridStartY + row * spacing + jitterY + 200,
    };
  });

  // Issues scattered around with deterministic radius variation
  typeGroups.issue.forEach((node, i) => {
    const angle = (i / Math.max(typeGroups.issue.length, 1)) * 2 * Math.PI;
    const radius = 350 + seededRandom(node.id) * 100;
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
          ? 'rgba(249, 115, 22, 0.4)'
          : 'rgba(107, 101, 96, 0.25)',
        strokeWidth: 1.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.type === 'tagged'
          ? 'rgba(249, 115, 22, 0.4)'
          : 'rgba(107, 101, 96, 0.3)',
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
      <div className="w-full h-full flex items-center justify-center bg-[#FAF8F5]">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-orange-500 flex items-center justify-center"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </motion.div>
          <p className="text-[#2D2A26] font-medium">Loading knowledge graph...</p>
          <p className="text-[#6B6560] text-sm mt-1">Mapping your AI memory</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#FAF8F5]">
        <div className="text-center max-w-md p-8 rounded-2xl border border-red-200 bg-red-50">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium mb-2">{error}</p>
          <p className="text-[#6B6560] text-sm">Make sure the backend is running on port 8090</p>
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
        <div className="rounded-2xl p-4 border border-[#E8E0D4] bg-white shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium text-[#2D2A26]">Knowledge Graph</span>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-500">
                {stats?.sessions || 0}
              </div>
              <div className="text-xs text-[#6B6560] mt-0.5">Sessions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[#2D2A26]">
                {stats?.learnings || 0}
              </div>
              <div className="text-xs text-[#6B6560] mt-0.5">Learnings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-400">
                {stats?.tags || 0}
              </div>
              <div className="text-xs text-[#6B6560] mt-0.5">Tags</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="rounded-2xl p-4 border border-[#E8E0D4] bg-white shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-[#6B6560]" />
            <span className="text-sm font-medium text-[#2D2A26]">Filters</span>
            <Badge variant="secondary" className="ml-auto bg-[#F5F0E8] text-[#6B6560] text-xs">
              {visibleCount}/{totalCount}
            </Badge>
          </div>
          <div className="space-y-2">
            <FilterButton
              active={showSessions}
              onClick={() => setShowSessions(!showSessions)}
              color="from-orange-500 to-orange-600"
              label="Sessions"
              count={stats?.sessions || 0}
            />
            <FilterButton
              active={showLearnings}
              onClick={() => setShowLearnings(!showLearnings)}
              color="from-[#2D2A26] to-[#3d3a36]"
              label="Learnings"
              count={stats?.learnings || 0}
            />
            <FilterButton
              active={showTags}
              onClick={() => setShowTags(!showTags)}
              color="from-orange-400 to-orange-500"
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
        <div className="rounded-2xl p-2 border border-[#E8E0D4] bg-white shadow-sm flex flex-col gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => zoomIn({ duration: 300 })}
            className="h-9 w-9 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => zoomOut({ duration: 300 })}
            className="h-9 w-9 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <div className="h-px bg-[#E8E0D4] my-1" />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleFitView}
            className="h-9 w-9 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </motion.div>

      {/* Interaction hint */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 text-xs text-[#6B6560] bg-white/90 px-4 py-2 rounded-full border border-[#E8E0D4] shadow-sm"
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
        <Background color="rgba(232, 224, 212, 0.5)" gap={32} size={1} />
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
          ? 'bg-[#F5F0E8] border border-[#E8E0D4]'
          : 'opacity-50 hover:opacity-75'
      }`}
    >
      <div className={`w-4 h-4 rounded bg-gradient-to-r ${color}`} />
      <span className="text-sm text-[#2D2A26] flex-1 text-left">{label}</span>
      <span className="text-xs text-[#6B6560]">{count}</span>
      {active ? (
        <Eye className="w-3.5 h-3.5 text-[#6B6560]" />
      ) : (
        <EyeOff className="w-3.5 h-3.5 text-[#9a918a]" />
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
