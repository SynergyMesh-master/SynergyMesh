/**
 * DAGBuilder Module - Semantic Workflow DAG Construction
 * 
 * Builds directed acyclic graphs for workflow orchestration.
 * Supports dependency resolution, cycle detection, and topological sorting.
 * 
 * Performance Target: <10ms DAG construction
 */

import { EventEmitter } from 'events';

/**
 * DAG node representing a workflow task
 */
export interface DAGNode {
  id: string;
  name: string;
  type: string;
  dependencies: string[];
  metadata: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

/**
 * DAG edge representing dependency relationship
 */
export interface DAGEdge {
  from: string;
  to: string;
  type: 'dependency' | 'data_flow' | 'control_flow';
  metadata?: Record<string, any>;
}

/**
 * Complete DAG definition
 */
export interface DAGDefinition {
  id: string;
  name: string;
  version: string;
  nodes: DAGNode[];
  edges: DAGEdge[];
  metadata: {
    created_at: string;
    updated_at: string;
    author: string;
  };
}

/**
 * DAG validation result
 */
export interface DAGValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  cycles?: string[][];
}

/**
 * DAGBuilder implementation with cycle detection and topological sorting
 */
export class DAGBuilder extends EventEmitter {
  private nodes: Map<string, DAGNode>;
  private edges: Map<string, DAGEdge[]>;
  private adjacencyList: Map<string, Set<string>>;

  constructor() {
    super();
    this.nodes = new Map();
    this.edges = new Map();
    this.adjacencyList = new Map();
  }

  /**
   * Add node to DAG
   */
  addNode(node: DAGNode): void {
    try {
      if (this.nodes.has(node.id)) {
        throw new Error(`Node ${node.id} already exists`);
      }
      
      this.nodes.set(node.id, node);
      this.adjacencyList.set(node.id, new Set());
      
      this.emit('node_added', { node_id: node.id, node_name: node.name });
    } catch (error) {
      this.emit('error', {
        operation: 'add_node',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Add edge to DAG
   */
  addEdge(edge: DAGEdge): void {
    try {
      if (!this.nodes.has(edge.from)) {
        throw new Error(`Source node ${edge.from} does not exist`);
      }
      
      if (!this.nodes.has(edge.to)) {
        throw new Error(`Target node ${edge.to} does not exist`);
      }
      
      // Add to edges map
      if (!this.edges.has(edge.from)) {
        this.edges.set(edge.from, []);
      }
      this.edges.get(edge.from)!.push(edge);
      
      // Update adjacency list
      this.adjacencyList.get(edge.from)!.add(edge.to);
      
      // Update node dependencies
      const targetNode = this.nodes.get(edge.to)!;
      if (!targetNode.dependencies.includes(edge.from)) {
        targetNode.dependencies.push(edge.from);
      }
      
      this.emit('edge_added', { from: edge.from, to: edge.to, type: edge.type });
    } catch (error) {
      this.emit('error', {
        operation: 'add_edge',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Build DAG from definition
   */
  buildFromDefinition(definition: DAGDefinition): void {
    const startTime = Date.now();
    
    try {
      this.emit('building_dag', { dag_id: definition.id });
      
      // Clear existing data
      this.clear();
      
      // Add all nodes
      for (const node of definition.nodes) {
        this.addNode(node);
      }
      
      // Add all edges
      for (const edge of definition.edges) {
        this.addEdge(edge);
      }
      
      // Validate DAG
      const validation = this.validate();
      if (!validation.valid) {
        throw new Error(`Invalid DAG: ${validation.errors.join(', ')}`);
      }
      
      const duration = Date.now() - startTime;
      
      this.emit('dag_built', {
        dag_id: definition.id,
        nodes_count: definition.nodes.length,
        edges_count: definition.edges.length,
        duration_ms: duration
      });
    } catch (error) {
      this.emit('error', {
        operation: 'build_from_definition',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Validate DAG structure
   */
  validate(): DAGValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    try {
      // Check for cycles
      const cycles = this.detectCycles();
      if (cycles.length > 0) {
        errors.push(`DAG contains ${cycles.length} cycle(s)`);
        return { valid: false, errors, warnings, cycles };
      }
      
      // Check for orphaned nodes
      const orphanedNodes = this.findOrphanedNodes();
      if (orphanedNodes.length > 0) {
        warnings.push(`Found ${orphanedNodes.length} orphaned node(s): ${orphanedNodes.join(', ')}`);
      }
      
      // Check for missing dependencies
      for (const [nodeId, node] of this.nodes.entries()) {
        for (const depId of node.dependencies) {
          if (!this.nodes.has(depId)) {
            errors.push(`Node ${nodeId} has missing dependency: ${depId}`);
          }
        }
      }
      
      this.emit('validation_complete', {
        valid: errors.length === 0,
        errors_count: errors.length,
        warnings_count: warnings.length
      });
      
      return {
        valid: errors.length === 0,
        errors,
        warnings
      };
    } catch (error) {
      this.emit('error', {
        operation: 'validate',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Detect cycles in DAG using DFS
   */
  private detectCycles(): string[][] {
    const cycles: string[][] = [];
    const visited = new Set<string>();
    const recursionStack = new Set<string>();
    const currentPath: string[] = [];
    
    const dfs = (nodeId: string): boolean => {
      visited.add(nodeId);
      recursionStack.add(nodeId);
      currentPath.push(nodeId);
      
      const neighbors = this.adjacencyList.get(nodeId) || new Set();
      
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          if (dfs(neighbor)) {
            return true;
          }
        } else if (recursionStack.has(neighbor)) {
          // Found cycle
          const cycleStart = currentPath.indexOf(neighbor);
          const cycle = currentPath.slice(cycleStart);
          cycles.push([...cycle, neighbor]);
          return true;
        }
      }
      
      recursionStack.delete(nodeId);
      currentPath.pop();
      return false;
    };
    
    for (const nodeId of this.nodes.keys()) {
      if (!visited.has(nodeId)) {
        dfs(nodeId);
      }
    }
    
    return cycles;
  }

  /**
   * Find orphaned nodes (no incoming or outgoing edges)
   */
  private findOrphanedNodes(): string[] {
    const orphaned: string[] = [];
    
    for (const [nodeId, neighbors] of this.adjacencyList.entries()) {
      const hasOutgoing = neighbors.size > 0;
      const hasIncoming = Array.from(this.adjacencyList.values())
        .some(set => set.has(nodeId));
      
      if (!hasOutgoing && !hasIncoming) {
        orphaned.push(nodeId);
      }
    }
    
    return orphaned;
  }

  /**
   * Topological sort using Kahn's algorithm
   */
  topologicalSort(): string[] {
    const startTime = Date.now();
    
    try {
      const inDegree = new Map<string, number>();
      const queue: string[] = [];
      const result: string[] = [];
      
      // Calculate in-degree for each node
      for (const nodeId of this.nodes.keys()) {
        inDegree.set(nodeId, 0);
      }
      
      for (const neighbors of this.adjacencyList.values()) {
        for (const neighbor of neighbors) {
          inDegree.set(neighbor, (inDegree.get(neighbor) || 0) + 1);
        }
      }
      
      // Add nodes with in-degree 0 to queue
      for (const [nodeId, degree] of inDegree.entries()) {
        if (degree === 0) {
          queue.push(nodeId);
        }
      }
      
      // Process queue
      while (queue.length > 0) {
        const nodeId = queue.shift()!;
        result.push(nodeId);
        
        const neighbors = this.adjacencyList.get(nodeId) || new Set();
        for (const neighbor of neighbors) {
          const newDegree = (inDegree.get(neighbor) || 0) - 1;
          inDegree.set(neighbor, newDegree);
          
          if (newDegree === 0) {
            queue.push(neighbor);
          }
        }
      }
      
      // Check if all nodes are included
      if (result.length !== this.nodes.size) {
        throw new Error('DAG contains cycle, cannot perform topological sort');
      }
      
      const duration = Date.now() - startTime;
      
      this.emit('topological_sort_complete', {
        nodes_count: result.length,
        duration_ms: duration
      });
      
      return result;
    } catch (error) {
      this.emit('error', {
        operation: 'topological_sort',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Get execution order with parallel stages
   */
  getExecutionStages(): string[][] {
    try {
      const inDegree = new Map<string, number>();
      const stages: string[][] = [];
      
      // Calculate in-degree
      for (const nodeId of this.nodes.keys()) {
        inDegree.set(nodeId, 0);
      }
      
      for (const neighbors of this.adjacencyList.values()) {
        for (const neighbor of neighbors) {
          inDegree.set(neighbor, (inDegree.get(neighbor) || 0) + 1);
        }
      }
      
      // Process stages
      while (inDegree.size > 0) {
        const currentStage: string[] = [];
        
        // Find all nodes with in-degree 0
        for (const [nodeId, degree] of inDegree.entries()) {
          if (degree === 0) {
            currentStage.push(nodeId);
          }
        }
        
        if (currentStage.length === 0) {
          throw new Error('DAG contains cycle');
        }
        
        stages.push(currentStage);
        
        // Remove processed nodes and update in-degrees
        for (const nodeId of currentStage) {
          inDegree.delete(nodeId);
          
          const neighbors = this.adjacencyList.get(nodeId) || new Set();
          for (const neighbor of neighbors) {
            if (inDegree.has(neighbor)) {
              inDegree.set(neighbor, (inDegree.get(neighbor) || 0) - 1);
            }
          }
        }
      }
      
      this.emit('execution_stages_computed', {
        stages_count: stages.length,
        max_parallelism: Math.max(...stages.map(s => s.length))
      });
      
      return stages;
    } catch (error) {
      this.emit('error', {
        operation: 'get_execution_stages',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Get DAG definition
   */
  getDefinition(): DAGDefinition {
    const nodes = Array.from(this.nodes.values());
    const edges: DAGEdge[] = [];
    
    for (const edgeList of this.edges.values()) {
      edges.push(...edgeList);
    }
    
    return {
      id: `dag:${Date.now()}`,
      name: 'Generated DAG',
      version: '1.0.0',
      nodes,
      edges,
      metadata: {
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        author: 'DAGBuilder'
      }
    };
  }

  /**
   * Get node by ID
   */
  getNode(nodeId: string): DAGNode | undefined {
    return this.nodes.get(nodeId);
  }

  /**
   * Get edges from node
   */
  getEdgesFrom(nodeId: string): DAGEdge[] {
    return this.edges.get(nodeId) || [];
  }

  /**
   * Get statistics
   */
  getStats(): {
    nodes_count: number;
    edges_count: number;
    max_depth: number;
  } {
    const edgesCount = Array.from(this.edges.values())
      .reduce((sum, edges) => sum + edges.length, 0);
    
    return {
      nodes_count: this.nodes.size,
      edges_count: edgesCount,
      max_depth: this.calculateMaxDepth()
    };
  }

  /**
   * Calculate maximum depth of DAG
   */
  private calculateMaxDepth(): number {
    const depths = new Map<string, number>();
    
    const calculateDepth = (nodeId: string): number => {
      if (depths.has(nodeId)) {
        return depths.get(nodeId)!;
      }
      
      const neighbors = this.adjacencyList.get(nodeId) || new Set();
      if (neighbors.size === 0) {
        depths.set(nodeId, 0);
        return 0;
      }
      
      let maxDepth = 0;
      for (const neighbor of neighbors) {
        maxDepth = Math.max(maxDepth, calculateDepth(neighbor) + 1);
      }
      
      depths.set(nodeId, maxDepth);
      return maxDepth;
    };
    
    let maxDepth = 0;
    for (const nodeId of this.nodes.keys()) {
      maxDepth = Math.max(maxDepth, calculateDepth(nodeId));
    }
    
    return maxDepth;
  }

  /**
   * Clear DAG
   */
  clear(): void {
    this.nodes.clear();
    this.edges.clear();
    this.adjacencyList.clear();
    this.emit('cleared');
  }
}

/**
 * Factory function to create DAGBuilder instance
 */
export function createDAGBuilder(): DAGBuilder {
  return new DAGBuilder();
}