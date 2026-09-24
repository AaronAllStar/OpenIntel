import React, { useMemo, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import { 
  User, 
  Globe, 
  Mail, 
  Network, 
  Link as LinkIcon, 
  Building2, 
  Search,
  Info
} from "lucide-react";

const KIND_COLORS = {
  profile: { bg: "rgba(14, 165, 233, 0.15)", border: "#0ea5e9", text: "#38bdf8", icon: User },
  domain: { bg: "rgba(16, 185, 129, 0.15)", border: "#10b981", text: "#34d399", icon: Globe },
  email: { bg: "rgba(245, 158, 11, 0.15)", border: "#f59e0b", text: "#fbbf24", icon: Mail },
  ip: { bg: "rgba(139, 92, 246, 0.15)", border: "#8b5cf6", text: "#a78bfa", icon: Network },
  url: { bg: "rgba(236, 72, 153, 0.15)", border: "#ec4899", text: "#f472b6", icon: LinkIcon },
  organization: { bg: "rgba(234, 88, 12, 0.15)", border: "#ea580c", text: "#fb923c", icon: Building2 },
};

export default function GraphView({
  entities = [],
  relationships = [],
  onSelectEntity,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedNodeData, setSelectedNodeData] = useState(null);

  // Generate initial node positions in a radial/grid layout
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes = entities.map((ent, idx) => {
      const angle = (idx / Math.max(1, entities.length)) * 2 * Math.PI;
      const radius = 240 + (idx % 2) * 60;
      const x = 350 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);

      const colorStyle = KIND_COLORS[ent.kind] || KIND_COLORS.profile;
      const isMatch = !searchTerm || ent.value.toLowerCase().includes(searchTerm.toLowerCase());

      return {
        id: ent.id,
        position: { x, y },
        data: {
          label: (
            <div className="flex items-center gap-2 px-3 py-2 text-left">
              <span style={{ color: colorStyle.border }}>
                <colorStyle.icon size={14} />
              </span>
              <div>
                <div className="text-[11px] font-semibold text-white truncate max-w-[140px]">
                  {ent.value}
                </div>
                <div className="text-[9px] uppercase font-mono tracking-wider opacity-70" style={{ color: colorStyle.text }}>
                  {ent.kind}
                </div>
              </div>
            </div>
          ),
          raw: ent,
        },
        style: {
          background: colorStyle.bg,
          border: `1.5px solid ${colorStyle.border}`,
          borderRadius: "12px",
          color: "#fff",
          boxShadow: isMatch ? "0 4px 15px rgba(0,0,0,0.4)" : "none",
          opacity: isMatch ? 1 : 0.25,
          cursor: "pointer",
        },
      };
    });

    const edges = relationships.map((rel) => ({
      id: rel.id,
      source: rel.source_entity_id,
      target: rel.target_entity_id,
      label: rel.predicate.replace(/_/g, " "),
      animated: true,
      style: { stroke: "rgba(56, 189, 248, 0.4)", strokeWidth: 1.5 },
      labelStyle: { fill: "#94a3b8", fontSize: 10, fontWeight: 500, fontFamily: "sans-serif" },
      labelBgStyle: { fill: "#0c111d", fillOpacity: 0.9, rx: 4, ry: 4 },
    }));

    return { initialNodes: nodes, initialEdges: edges };
  }, [entities, relationships, searchTerm]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClick = useCallback(
    (_, node) => {
      setSelectedNodeData(node.data.raw);
      if (onSelectEntity) {
        onSelectEntity(node.data.raw);
      }
    },
    [onSelectEntity]
  );

  return (
    <div className="relative w-full h-[600px] glass-panel overflow-hidden border border-white/10 rounded-2xl">
      {/* Search Bar overlay */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
        <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 shadow-lg">
          <Search size={14} className="text-slate-400" />
          <input
            type="text"
            placeholder="Search graph entities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-48 font-mono"
          />
        </div>
        <div className="text-[11px] text-slate-400 font-mono bg-slate-900/90 px-3 py-1.5 rounded-xl border border-white/10">
          {entities.length} nodes · {relationships.length} edges
        </div>
      </div>

      {/* Inspector Drawer overlay on node click */}
      {selectedNodeData && (
        <div className="absolute top-4 right-4 z-10 w-72 p-4 glass-panel bg-slate-900/95 border-sky-500/30 text-left shadow-2xl animate-fadeIn">
          <div className="flex items-start justify-between mb-2">
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 font-semibold">
              {selectedNodeData.kind}
            </span>
            <button
              onClick={() => setSelectedNodeData(null)}
              className="text-slate-500 hover:text-slate-300 text-xs"
            >
              ✕
            </button>
          </div>
          <div className="font-semibold text-white text-xs break-all mb-2">
            {selectedNodeData.value}
          </div>
          <div className="text-[11px] text-slate-400 space-y-1">
            <div>
              Confidence: <strong className="text-slate-200">{selectedNodeData.confidence}</strong>
            </div>
            {selectedNodeData.attributes && Object.keys(selectedNodeData.attributes).length > 0 && (
              <div className="mt-2 pt-2 border-t border-white/5">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                  Attributes
                </div>
                <div className="font-mono text-[10px] text-slate-300 space-y-0.5 max-h-28 overflow-y-auto">
                  {Object.entries(selectedNodeData.attributes).map(([k, v]) => (
                    <div key={k}>
                      <span className="text-slate-500">{k}:</span> {String(v)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="bg-slate-900 border-white/10 fill-slate-300" />
        <MiniMap
          nodeColor={(n) => n.style?.border || "#38bdf8"}
          maskColor="rgba(15, 23, 42, 0.7)"
          className="bg-slate-950 border-white/10 rounded-xl overflow-hidden"
        />
      </ReactFlow>
    </div>
  );
}
