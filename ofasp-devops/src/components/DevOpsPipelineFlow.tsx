import React, { useState, useEffect, useRef } from 'react';
import { useI18n } from '../hooks/useI18n';

interface PipelineNode {
  id: string;
  label: string;
  type: 'process' | 'decision' | 'artifact' | 'external';
  status: 'idle' | 'running' | 'success' | 'failed' | 'warning';
  position: { x: number; y: number };
  details?: string;
  progress?: number;
  duration?: string;
}

interface PipelineEdge {
  from: string;
  to: string;
  type: 'success' | 'failure' | 'feedback' | 'standard';
  label?: string;
  animated?: boolean;
}

interface DevOpsPipelineFlowProps {
  isDarkMode?: boolean;
  onNodeClick?: (nodeId: string) => void;
}

const DevOpsPipelineFlow: React.FC<DevOpsPipelineFlowProps> = ({ isDarkMode = false, onNodeClick }) => {
  const { t } = useI18n();
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<PipelineNode[]>([]);
  const [edges, setEdges] = useState<PipelineEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [currentSimulationStep, setCurrentSimulationStep] = useState(0);

  // Initialize pipeline structure
  useEffect(() => {
    const pipelineNodes: PipelineNode[] = [
      // Main Flow
      { id: 'commit', label: 'Code Commit', type: 'process', status: 'idle', position: { x: 180, y: 200 } },
      { id: 'build-artifact', label: 'Build Artifact', type: 'artifact', status: 'idle', position: { x: 310, y: 200 } },
      { id: 'build', label: 'Build Check', type: 'process', status: 'idle', position: { x: 440, y: 200 } },
      { id: 'build-decision', label: 'Build Success?', type: 'decision', status: 'idle', position: { x: 530, y: 200 } },
      { id: 'test', label: 'Testing', type: 'process', status: 'idle', position: { x: 620, y: 200 } },
      { id: 'test-decision', label: 'Tests Pass?', type: 'decision', status: 'idle', position: { x: 710, y: 200 } },
      { id: 'security', label: 'Security Scan', type: 'process', status: 'idle', position: { x: 800, y: 200 } },
      { id: 'security-decision', label: 'Security Pass?', type: 'decision', status: 'idle', position: { x: 890, y: 200 } },
      { id: 'deploy', label: 'Deploy', type: 'process', status: 'idle', position: { x: 980, y: 200 } },
      { id: 'deploy-decision', label: 'Deploy Success?', type: 'decision', status: 'idle', position: { x: 1070, y: 200 } },
      { id: 'production', label: 'Production Ready', type: 'process', status: 'idle', position: { x: 1170, y: 200 } },
      
      // External Inputs
      { id: 'devops-docs', label: 'DevOps Docs', type: 'external', status: 'idle', position: { x: 90, y: 350 } },
      { id: 'ci-cd-tools', label: 'CI/CD Tools', type: 'external', status: 'idle', position: { x: 290, y: 350 } },
      { id: 'infrastructure', label: 'Infrastructure', type: 'external', status: 'idle', position: { x: 490, y: 425 } },
      { id: 'monitoring', label: 'Monitoring', type: 'external', status: 'idle', position: { x: 1140, y: 425 } }
    ];

    const pipelineEdges: PipelineEdge[] = [
      // Main flow
      { from: 'commit', to: 'build-artifact', type: 'standard' },
      { from: 'build-artifact', to: 'build', type: 'standard' },
      { from: 'build', to: 'build-decision', type: 'standard' },
      { from: 'build-decision', to: 'test', type: 'success', label: 'Yes' },
      { from: 'test', to: 'test-decision', type: 'standard' },
      { from: 'test-decision', to: 'security', type: 'success', label: 'Yes' },
      { from: 'security', to: 'security-decision', type: 'standard' },
      { from: 'security-decision', to: 'deploy', type: 'success', label: 'Yes' },
      { from: 'deploy', to: 'deploy-decision', type: 'standard' },
      { from: 'deploy-decision', to: 'production', type: 'success', label: 'Yes' },
      
      // Failure feedback loops - each goes to different recovery point
      { from: 'build-decision', to: 'build-artifact', type: 'failure', label: 'No' },
      { from: 'test-decision', to: 'build', type: 'failure', label: 'No' },
      { from: 'security-decision', to: 'test', type: 'failure', label: 'No' },
      { from: 'deploy-decision', to: 'security', type: 'failure', label: 'No' },
      
      // External connections
      { from: 'devops-docs', to: 'commit', type: 'standard' },
      { from: 'ci-cd-tools', to: 'build-artifact', type: 'standard' },
      { from: 'infrastructure', to: 'security', type: 'standard' },
      { from: 'monitoring', to: 'deploy', type: 'standard' }
    ];

    setNodes(pipelineNodes);
    setEdges(pipelineEdges);
  }, []);

  // Fetch real-time pipeline status
  useEffect(() => {
    const fetchPipelineStatus = async () => {
      try {
        const response = await fetch('/api/pipeline-flow-status');
        if (response.ok) {
          const data = await response.json();
          // Update nodes with real-time status
          setNodes(prevNodes => 
            prevNodes.map(node => ({
              ...node,
              status: data[node.id]?.status || node.status,
              progress: data[node.id]?.progress,
              duration: data[node.id]?.duration,
              details: data[node.id]?.details
            }))
          );
        }
      } catch (error) {
        console.error('Failed to fetch pipeline status:', error);
      }
    };

    // Initial fetch
    fetchPipelineStatus();

    // Set up polling every 5 seconds
    const interval = setInterval(fetchPipelineStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  // Pipeline simulation
  const runSimulation = () => {
    setSimulationRunning(true);
    setCurrentSimulationStep(0);
    
    const steps = [
      'commit', 'build-artifact', 'build', 'build-decision',
      'test', 'test-decision', 'security', 'security-decision',
      'deploy', 'deploy-decision', 'production'
    ];

    let stepIndex = 0;
    const simulationInterval = setInterval(() => {
      if (stepIndex < steps.length) {
        const currentNodeId = steps[stepIndex];
        
        // Update node status
        setNodes(prevNodes =>
          prevNodes.map(node => {
            if (node.id === currentNodeId) {
              return { ...node, status: 'running', progress: 50 };
            } else if (steps.indexOf(node.id) < stepIndex && steps.includes(node.id)) {
              return { ...node, status: 'success', progress: 100 };
            }
            return node;
          })
        );

        // Animate edges
        setEdges(prevEdges =>
          prevEdges.map(edge => ({
            ...edge,
            animated: edge.from === currentNodeId || edge.to === currentNodeId
          }))
        );

        stepIndex++;
      } else {
        // Complete simulation
        clearInterval(simulationInterval);
        setSimulationRunning(false);
        
        // Mark all as success
        setNodes(prevNodes =>
          prevNodes.map(node => ({
            ...node,
            status: steps.includes(node.id) ? 'success' : node.status,
            progress: steps.includes(node.id) ? 100 : node.progress
          }))
        );
      }
    }, 1000);
  };

  // Reset simulation
  const resetSimulation = () => {
    setSimulationRunning(false);
    setCurrentSimulationStep(0);
    setNodes(prevNodes =>
      prevNodes.map(node => ({
        ...node,
        status: 'idle',
        progress: undefined
      }))
    );
    setEdges(prevEdges =>
      prevEdges.map(edge => ({
        ...edge,
        animated: false
      }))
    );
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
    if (onNodeClick) {
      onNodeClick(nodeId);
    }
  };

  const handleNodeHover = (nodeId: string, event: React.MouseEvent) => {
    setHoveredNode(nodeId);
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) {
      setTooltipPosition({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top - 10
      });
      setShowTooltip(true);
    }
  };

  const handleNodeLeave = () => {
    setHoveredNode(null);
    setShowTooltip(false);
  };

  const getNodeColor = (node: PipelineNode) => {
    if (node.type === 'external') return '#e5e7eb';
    
    switch (node.status) {
      case 'running': return '#3b82f6';
      case 'success': return '#10b981';
      case 'failed': return '#ef4444';
      case 'warning': return '#f59e0b';
      default: return node.type === 'decision' ? '#f472b6' : '#3b82f6';
    }
  };

  const getNodeStroke = (node: PipelineNode) => {
    if (node.id === selectedNode) return '#1e40af';
    if (node.type === 'external') return '#9ca3af';
    
    switch (node.status) {
      case 'running': return '#1e40af';
      case 'success': return '#059669';
      case 'failed': return '#dc2626';
      case 'warning': return '#d97706';
      default: return node.type === 'decision' ? '#be185d' : '#1e40af';
    }
  };

  const getEdgeColor = (edge: PipelineEdge) => {
    switch (edge.type) {
      case 'success': return '#10b981';
      case 'failure': return '#ef4444';
      case 'feedback': return '#f59e0b';
      default: return '#374151';
    }
  };

  const renderNode = (node: PipelineNode) => {
    const isHovered = hoveredNode === node.id;
    const isSelected = selectedNode === node.id;
    const scale = isHovered ? 1.05 : 1;

    if (node.type === 'decision') {
      // Diamond shape for decision nodes
      return (
        <g
          key={node.id}
          transform={`translate(${node.position.x}, ${node.position.y})`}
          onClick={() => handleNodeClick(node.id)}
          onMouseEnter={(e) => handleNodeHover(node.id, e)}
          onMouseLeave={handleNodeLeave}
          style={{ cursor: 'pointer' }}
        >
          <g transform={`scale(${scale})`}>
            <rect
              x="-20"
              y="-20"
              width="40"
              height="40"
              fill={getNodeColor(node)}
              stroke={getNodeStroke(node)}
              strokeWidth={isSelected ? 3 : 2}
              transform="rotate(45)"
              className={node.status === 'running' ? 'animate-pulse' : ''}
            />
            <text
              x="0"
              y="5"
              textAnchor="middle"
              className="text-xs font-semibold"
              fill="#1f2937"
            >
              {node.label.split(' ')[0]}
            </text>
            <text
              x="0"
              y="18"
              textAnchor="middle"
              className="text-xs font-semibold"
              fill="#1f2937"
            >
              {node.label.split(' ')[1]}
            </text>
          </g>
        </g>
      );
    } else if (node.type === 'artifact') {
      // Dashed box for artifacts
      return (
        <g
          key={node.id}
          transform={`translate(${node.position.x}, ${node.position.y})`}
          onClick={() => handleNodeClick(node.id)}
          onMouseEnter={(e) => handleNodeHover(node.id, e)}
          onMouseLeave={handleNodeLeave}
          style={{ cursor: 'pointer' }}
        >
          <rect
            x="-60"
            y="-40"
            width="120"
            height="80"
            fill="none"
            stroke="#6b7280"
            strokeWidth="2"
            strokeDasharray="5,5"
          />
          <rect
            x="-50"
            y="-30"
            width="100"
            height="20"
            fill="#f9fafb"
            stroke="#d1d5db"
          />
          <text
            x="0"
            y="-15"
            textAnchor="middle"
            className="text-xs"
            fill="#6b7280"
          >
            {node.label}
          </text>
          {node.progress !== undefined && (
            <rect
              x="-50"
              y="0"
              width={100 * (node.progress / 100)}
              height="4"
              fill={getNodeColor(node)}
            />
          )}
        </g>
      );
    } else {
      // Circle for process nodes
      return (
        <g
          key={node.id}
          transform={`translate(${node.position.x}, ${node.position.y})`}
          onClick={() => handleNodeClick(node.id)}
          onMouseEnter={(e) => handleNodeHover(node.id, e)}
          onMouseLeave={handleNodeLeave}
          style={{ cursor: 'pointer' }}
        >
          <g transform={`scale(${scale})`}>
            <circle
              r={node.type === 'external' ? 40 : 30}
              fill={getNodeColor(node)}
              stroke={getNodeStroke(node)}
              strokeWidth={isSelected ? 3 : 2}
              className={node.status === 'running' ? 'animate-pulse' : ''}
            />
            <text
              y="5"
              textAnchor="middle"
              className={`text-xs font-semibold ${node.type === 'external' ? 'text-gray-700' : 'text-white'}`}
            >
              {node.label}
            </text>
            {node.progress !== undefined && node.type !== 'external' && (
              <>
                <circle
                  r="25"
                  fill="none"
                  stroke="rgba(255,255,255,0.3)"
                  strokeWidth="4"
                />
                <circle
                  r="25"
                  fill="none"
                  stroke="white"
                  strokeWidth="4"
                  strokeDasharray={`${2 * Math.PI * 25 * (node.progress / 100)} ${2 * Math.PI * 25}`}
                  transform="rotate(-90)"
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
              </>
            )}
          </g>
        </g>
      );
    }
  };

  const renderEdge = (edge: PipelineEdge) => {
    const fromNode = nodes.find(n => n.id === edge.from);
    const toNode = nodes.find(n => n.id === edge.to);
    
    if (!fromNode || !toNode) return null;

    const dx = toNode.position.x - fromNode.position.x;
    const dy = toNode.position.y - fromNode.position.y;
    const angle = Math.atan2(dy, dx);
    
    // Calculate edge endpoints
    const fromRadius = fromNode.type === 'external' ? 40 : 30;
    const toRadius = toNode.type === 'external' ? 40 : 30;
    
    const x1 = fromNode.position.x + fromRadius * Math.cos(angle);
    const y1 = fromNode.position.y + fromRadius * Math.sin(angle);
    const x2 = toNode.position.x - toRadius * Math.cos(angle);
    const y2 = toNode.position.y - toRadius * Math.sin(angle);

    // Path for feedback loops - changed to dotted straight lines with different offsets
    if (edge.type === 'failure' || edge.type === 'feedback') {
      // Calculate different Y offsets for each failure path to avoid overlap
      let yOffset = 100;
      const failureEdgeColors = {
        'build-decision': '#ef4444',    // Red
        'test-decision': '#f97316',     // Orange  
        'security-decision': '#d946ef', // Magenta
        'deploy-decision': '#6366f1'    // Indigo
      };
      
      // Different Y offsets for each failure type
      if (edge.from === 'build-decision') yOffset = 80;
      else if (edge.from === 'test-decision') yOffset = 110;
      else if (edge.from === 'security-decision') yOffset = 140;
      else if (edge.from === 'deploy-decision') yOffset = 170;
      
      const midY = Math.max(y1, y2) + yOffset;
      const edgeColor = failureEdgeColors[edge.from as keyof typeof failureEdgeColors] || getEdgeColor(edge);
      
      return (
        <g key={`${edge.from}-${edge.to}`}>
          {/* Vertical line down */}
          <line
            x1={x1}
            y1={y1}
            x2={x1}
            y2={midY}
            stroke={edgeColor}
            strokeWidth="2"
            strokeDasharray="5,5"
            className={edge.animated ? 'animate-pulse' : ''}
          />
          {/* Horizontal line across */}
          <line
            x1={x1}
            y1={midY}
            x2={x2}
            y2={midY}
            stroke={edgeColor}
            strokeWidth="2"
            strokeDasharray="5,5"
            className={edge.animated ? 'animate-pulse' : ''}
          />
          {/* Vertical line up */}
          <line
            x1={x2}
            y1={midY}
            x2={x2}
            y2={y2}
            stroke={edgeColor}
            strokeWidth="2"
            strokeDasharray="5,5"
            markerEnd={`url(#arrowhead-failure-${edge.from})`}
            className={edge.animated ? 'animate-pulse' : ''}
          />
          {edge.label && (
            <text
              x={(x1 + x2) / 2}
              y={midY - 5}
              textAnchor="middle"
              className="text-xs font-medium"
              fill={edgeColor}
            >
              {edge.label} → {toNode.label}
            </text>
          )}
        </g>
      );
    }

    return (
      <g key={`${edge.from}-${edge.to}`}>
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={getEdgeColor(edge)}
          strokeWidth="2"
          markerEnd={`url(#arrowhead-${edge.type})`}
          className={edge.animated ? 'animate-pulse' : ''}
        />
        {edge.label && (
          <text
            x={(x1 + x2) / 2}
            y={(y1 + y2) / 2 - 5}
            textAnchor="middle"
            className="text-xs"
            fill={getEdgeColor(edge)}
          >
            {edge.label}
          </text>
        )}
      </g>
    );
  };

  const hoveredNodeData = nodes.find(n => n.id === hoveredNode);

  return (
    <div className="relative w-full h-full">

      {/* SVG Container */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        viewBox="0 0 1400 600"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Define arrow markers */}
        <defs>
          {/* Standard markers */}
          {['standard', 'success', 'failure', 'feedback'].map(type => (
            <marker
              key={`arrowhead-${type}`}
              id={`arrowhead-${type}`}
              markerWidth="10"
              markerHeight="7"
              refX="10"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill={type === 'success' ? '#10b981' : type === 'failure' ? '#ef4444' : type === 'feedback' ? '#f59e0b' : '#374151'}
              />
            </marker>
          ))}
          
          {/* Failure-specific markers with different colors */}
          <marker
            id="arrowhead-failure-build-decision"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#ef4444" />
          </marker>
          <marker
            id="arrowhead-failure-test-decision"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#f97316" />
          </marker>
          <marker
            id="arrowhead-failure-security-decision"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#d946ef" />
          </marker>
          <marker
            id="arrowhead-failure-deploy-decision"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
          </marker>
        </defs>

        {/* Title */}
        <text x="700" y="30" textAnchor="middle" className="text-2xl font-bold" fill="#1e293b">
          DevOps CI/CD Pipeline Workflow
        </text>

        {/* Subtitle */}
        <text x="700" y="55" textAnchor="middle" className="text-sm" fill="#6b7280">
          Real-time Pipeline Execution Monitor
        </text>

        {/* Render edges */}
        {edges.map(edge => renderEdge(edge))}

        {/* Render nodes */}
        {nodes.map(node => renderNode(node))}

        {/* Stage labels */}
        <text x="180" y="100" textAnchor="middle" className="text-sm font-semibold" fill="#3b82f6">
          CI/CD Pipeline Stages
        </text>
        <text x="310" y="120" textAnchor="middle" className="text-xs" fill="#6b7280">
          1. Source Control
        </text>
        <text x="440" y="120" textAnchor="middle" className="text-xs" fill="#6b7280">
          2. Build & Compile
        </text>
        <text x="620" y="120" textAnchor="middle" className="text-xs" fill="#6b7280">
          3. Automated Testing
        </text>
        <text x="800" y="120" textAnchor="middle" className="text-xs" fill="#6b7280">
          4. Security & Quality
        </text>
        <text x="980" y="120" textAnchor="middle" className="text-xs" fill="#6b7280">
          5. Deployment
        </text>

        {/* Feedback loop label */}
        <text x="700" y="380" textAnchor="middle" className="text-xs" fill="#f59e0b">
          Feedback loops for continuous improvement
        </text>
      </svg>

      {/* Tooltip */}
      {showTooltip && hoveredNodeData && (
        <div
          className="absolute bg-gray-900 text-white p-3 rounded-lg shadow-xl text-sm z-20 pointer-events-none"
          style={{
            left: tooltipPosition.x + 10,
            top: tooltipPosition.y
          }}
        >
          <div className="font-semibold mb-1">{hoveredNodeData.label}</div>
          <div className="text-xs space-y-1">
            <div>Status: {hoveredNodeData.status}</div>
            {hoveredNodeData.progress !== undefined && (
              <div>Progress: {hoveredNodeData.progress}%</div>
            )}
            {hoveredNodeData.duration && (
              <div>Duration: {hoveredNodeData.duration}</div>
            )}
            {hoveredNodeData.details && (
              <div className="mt-2 pt-2 border-t border-gray-700">
                {hoveredNodeData.details}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-lg shadow-lg p-4 max-w-sm border border-gray-200 dark:border-gray-700">
        <h4 className="font-semibold text-sm mb-3">Legend</h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500"></div>
              <span>Process Node</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-pink-500 transform rotate-45"></div>
              <span>Decision Point</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-dashed border-gray-500"></div>
              <span>Artifact</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-gray-300"></div>
              <span>External Input</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="font-medium text-xs mb-1">Failure Routes:</div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-red-500" style={{borderStyle: 'dashed', borderWidth: '1px 0'}}></div>
              <span>Build Fails</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-orange-500" style={{borderStyle: 'dashed', borderWidth: '1px 0'}}></div>
              <span>Test Fails</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-fuchsia-500" style={{borderStyle: 'dashed', borderWidth: '1px 0'}}></div>
              <span>Security Fails</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-indigo-500" style={{borderStyle: 'dashed', borderWidth: '1px 0'}}></div>
              <span>Deploy Fails</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DevOpsPipelineFlow;