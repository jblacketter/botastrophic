import { useState, useEffect, useRef } from 'react';
import { fetchRelationshipGraph, type GraphNode, type GraphEdge, type RelationshipGraph as GraphData } from '../api/client';

const BOT_COLORS: Record<string, string> = {
  ada_001: '#db2777',
  echo_001: '#0d9488',
  luna_001: '#4f46e5',
  marcus_001: '#d97706',
  rex_001: '#dc2626',
  sage_001: '#059669',
};

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const WIDTH = 400;
const HEIGHT = 300;
const NODE_RADIUS = 18;

function RelationshipGraphPanel() {
  const [data, setData] = useState<GraphData | null>(null);
  const [nodes, setNodes] = useState<SimNode[]>([]);
  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null);
  const animRef = useRef<number>(0);
  const simRunning = useRef(false);

  useEffect(() => {
    fetchRelationshipGraph()
      .then((g) => {
        setData(g);
        // Initialize node positions in a circle
        const n = g.nodes.length;
        const simNodes: SimNode[] = g.nodes.map((node, i) => ({
          ...node,
          x: WIDTH / 2 + Math.cos((2 * Math.PI * i) / n) * 80,
          y: HEIGHT / 2 + Math.sin((2 * Math.PI * i) / n) * 80,
          vx: 0,
          vy: 0,
        }));
        setNodes(simNodes);
        simRunning.current = true;
      })
      .catch((e) => console.error('Failed to load graph:', e));

    return () => {
      simRunning.current = false;
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, []);

  // Force simulation
  useEffect(() => {
    if (!data || nodes.length === 0) return;

    let tickCount = 0;
    const maxTicks = 200;
    const damping = 0.92;
    const repulsion = 3000;
    const attraction = 0.005;
    const centerGravity = 0.01;

    const tick = () => {
      if (!simRunning.current || tickCount >= maxTicks) return;
      tickCount++;

      const updated = [...nodes];

      // Repulsion between all pairs
      for (let i = 0; i < updated.length; i++) {
        for (let j = i + 1; j < updated.length; j++) {
          const dx = updated[j].x - updated[i].x;
          const dy = updated[j].y - updated[i].y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const force = repulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          updated[i].vx -= fx;
          updated[i].vy -= fy;
          updated[j].vx += fx;
          updated[j].vy += fy;
        }
      }

      // Attraction along edges
      const nodeMap = new Map(updated.map((n) => [n.id, n]));
      for (const edge of data.edges) {
        const src = nodeMap.get(edge.source);
        const tgt = nodeMap.get(edge.target);
        if (!src || !tgt) continue;
        const dx = tgt.x - src.x;
        const dy = tgt.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const force = dist * attraction * (1 + edge.interaction_count * 0.1);
        src.vx += (dx / Math.max(dist, 1)) * force;
        src.vy += (dy / Math.max(dist, 1)) * force;
        tgt.vx -= (dx / Math.max(dist, 1)) * force;
        tgt.vy -= (dy / Math.max(dist, 1)) * force;
      }

      // Center gravity + damping + bounds
      for (const node of updated) {
        node.vx += (WIDTH / 2 - node.x) * centerGravity;
        node.vy += (HEIGHT / 2 - node.y) * centerGravity;
        node.vx *= damping;
        node.vy *= damping;
        node.x = Math.max(NODE_RADIUS, Math.min(WIDTH - NODE_RADIUS, node.x + node.vx));
        node.y = Math.max(NODE_RADIUS, Math.min(HEIGHT - NODE_RADIUS, node.y + node.vy));
      }

      setNodes([...updated]);
      animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [data, nodes.length]);

  if (!data) return <div className="bg-gray-800 rounded-lg p-4 text-sm text-gray-400">Loading graph...</div>;
  if (data.nodes.length === 0) return null;

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  const edgeColor = (sentiment: number) => {
    if (sentiment > 0.2) return '#22c55e';
    if (sentiment < -0.2) return '#ef4444';
    return '#6b7280';
  };

  const getColor = (id: string) => BOT_COLORS[id] || '#6b7280';

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold mb-3">Relationships</h2>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" style={{ maxHeight: 300 }}>
        {/* Edges */}
        {data.edges.map((edge, i) => {
          const src = nodeMap.get(edge.source);
          const tgt = nodeMap.get(edge.target);
          if (!src || !tgt) return null;
          const isHovered = hoveredEdge === edge;
          return (
            <g key={i}>
              <line
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke={edgeColor(edge.sentiment)}
                strokeWidth={Math.max(1, Math.min(edge.interaction_count * 0.5, 4))}
                strokeDasharray={edge.interaction_count === 0 ? '4 4' : undefined}
                opacity={isHovered ? 1 : 0.5}
                onMouseEnter={() => setHoveredEdge(edge)}
                onMouseLeave={() => setHoveredEdge(null)}
                style={{ cursor: 'pointer' }}
              />
              {/* Invisible wider line for hover target */}
              <line
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke="transparent"
                strokeWidth={10}
                onMouseEnter={() => setHoveredEdge(edge)}
                onMouseLeave={() => setHoveredEdge(null)}
              />
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={NODE_RADIUS}
              fill={getColor(node.id)}
              opacity={0.9}
            />
            <text
              x={node.x}
              y={node.y}
              textAnchor="middle"
              dominantBaseline="central"
              fill="white"
              fontSize={9}
              fontWeight="bold"
            >
              {node.name.slice(0, 3)}
            </text>
            <text
              x={node.x}
              y={node.y + NODE_RADIUS + 10}
              textAnchor="middle"
              fill="#9ca3af"
              fontSize={8}
            >
              {node.name}
            </text>
          </g>
        ))}
      </svg>

      {/* Hover tooltip */}
      {hoveredEdge && (
        <div className="mt-2 text-xs text-gray-400 bg-gray-700 rounded p-2">
          <span className="text-gray-200">{hoveredEdge.source}</span>
          {' <-> '}
          <span className="text-gray-200">{hoveredEdge.target}</span>
          {' | '}
          Interactions: {hoveredEdge.interaction_count}
          {' | '}
          Sentiment: <span className={hoveredEdge.sentiment > 0 ? 'text-green-400' : hoveredEdge.sentiment < 0 ? 'text-red-400' : ''}>
            {hoveredEdge.sentiment > 0 ? '+' : ''}{hoveredEdge.sentiment}
          </span>
          {hoveredEdge.follows && ' | Follows'}
        </div>
      )}

      {/* Legend */}
      <div className="flex gap-3 mt-2 text-[10px] text-gray-500">
        <span><span className="inline-block w-3 h-0.5 bg-green-500 mr-1" />Positive</span>
        <span><span className="inline-block w-3 h-0.5 bg-gray-500 mr-1" />Neutral</span>
        <span><span className="inline-block w-3 h-0.5 bg-red-500 mr-1" />Negative</span>
      </div>
    </div>
  );
}

export default RelationshipGraphPanel;
