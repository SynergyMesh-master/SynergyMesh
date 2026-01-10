/**
 * HybridRAG Module - Hybrid Retrieval Augmented Generation
 * 
 * Combines vector-based and graph-based retrieval for optimal results.
 * Implements context merging, relevance fusion, and multi-modal retrieval.
 * 
 * Performance Target: <50ms retrieval, >95% relevance
 */

import { EventEmitter } from 'events';
import { VectorRAG, VectorChunk, QueryConfig, RetrievalResult } from '../vector/vector-rag';
import { GraphRAG, KnowledgeTriplet, GraphQueryConfig, GraphRetrievalResult } from '../graph/graph-rag';

/**
 * Hybrid context artifact type
 */
export interface HybridContext {
  id: string;
  vector_chunks: VectorChunk[];
  knowledge_triplets: KnowledgeTriplet[];
  merged_context: string;
  metadata: {
    query: string;
    timestamp: string;
    vector_score: number;
    graph_score: number;
    fusion_score: number;
  };
}

/**
 * Hybrid query configuration
 */
export interface HybridQueryConfig {
  query: string;
  vector_weight?: number;
  graph_weight?: number;
  top_k?: number;
  max_depth?: number;
  fusion_method?: 'rrf' | 'weighted' | 'cascade';
}

/**
 * Hybrid retrieval result
 */
export interface HybridRetrievalResult {
  context: HybridContext;
  vector_result: RetrievalResult;
  graph_result: GraphRetrievalResult;
  total_retrieval_time_ms: number;
  fusion_score: number;
}

/**
 * HybridRAG implementation with multi-modal retrieval and context fusion
 */
export class HybridRAG extends EventEmitter {
  private vectorRAG: VectorRAG;
  private graphRAG: GraphRAG;
  private initialized: boolean;

  constructor(vectorRAG: VectorRAG, graphRAG: GraphRAG) {
    super();
    this.vectorRAG = vectorRAG;
    this.graphRAG = graphRAG;
    this.initialized = false;
  }

  /**
   * Initialize hybrid RAG system
   */
  async initialize(): Promise<void> {
    const startTime = Date.now();
    
    try {
      this.emit('initializing');
      
      // Initialize both vector and graph RAG
      await Promise.all([
        this.vectorRAG.initialize(),
        this.graphRAG.initialize()
      ]);
      
      this.initialized = true;
      const duration = Date.now() - startTime;
      
      this.emit('initialized', { duration_ms: duration });
    } catch (error) {
      this.emit('error', {
        operation: 'initialize',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Hybrid query with vector and graph retrieval
   */
  async query(config: HybridQueryConfig): Promise<HybridRetrievalResult> {
    const startTime = Date.now();
    
    try {
      if (!this.initialized) {
        throw new Error('HybridRAG not initialized');
      }
      
      const vectorWeight = config.vector_weight ?? 0.6;
      const graphWeight = config.graph_weight ?? 0.4;
      const fusionMethod = config.fusion_method || 'weighted';
      
      // Parallel retrieval from both sources
      const [vectorResult, graphResult] = await Promise.all([
        this.vectorRAG.query({
          query: config.query,
          top_k: config.top_k || 5,
          rerank: true
        } as QueryConfig),
        this.graphRAG.query({
          query: config.query,
          max_depth: config.max_depth || 2,
          max_results: config.top_k || 5
        } as GraphQueryConfig)
      ]);
      
      // Merge and fuse results
      const context = await this.mergeContext(
        vectorResult,
        graphResult,
        config.query,
        vectorWeight,
        graphWeight,
        fusionMethod
      );
      
      const duration = Date.now() - startTime;
      
      const result: HybridRetrievalResult = {
        context,
        vector_result: vectorResult,
        graph_result: graphResult,
        total_retrieval_time_ms: duration,
        fusion_score: context.metadata.fusion_score
      };
      
      this.emit('query_complete', {
        query: config.query,
        vector_chunks: vectorResult.chunks.length,
        graph_triplets: graphResult.triplets.length,
        fusion_score: context.metadata.fusion_score,
        duration_ms: duration
      });
      
      return result;
    } catch (error) {
      this.emit('error', {
        operation: 'query',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Merge vector and graph contexts
   */
  private async mergeContext(
    vectorResult: RetrievalResult,
    graphResult: GraphRetrievalResult,
    query: string,
    vectorWeight: number,
    graphWeight: number,
    fusionMethod: string
  ): Promise<HybridContext> {
    try {
      // Calculate scores
      const vectorScore = this.calculateVectorScore(vectorResult);
      const graphScore = this.calculateGraphScore(graphResult);
      
      // Fusion score based on method
      let fusionScore: number;
      
      switch (fusionMethod) {
        case 'rrf':
          fusionScore = this.reciprocalRankFusion(vectorScore, graphScore);
          break;
        case 'cascade':
          fusionScore = this.cascadeFusion(vectorScore, graphScore);
          break;
        case 'weighted':
        default:
          fusionScore = vectorWeight * vectorScore + graphWeight * graphScore;
      }
      
      // Merge contexts
      const mergedContext = this.buildMergedContext(
        vectorResult.chunks,
        graphResult.triplets
      );
      
      const context: HybridContext = {
        id: `hybrid:${Date.now()}`,
        vector_chunks: vectorResult.chunks,
        knowledge_triplets: graphResult.triplets,
        merged_context: mergedContext,
        metadata: {
          query,
          timestamp: new Date().toISOString(),
          vector_score: vectorScore,
          graph_score: graphScore,
          fusion_score: fusionScore
        }
      };
      
      this.emit('context_merged', {
        query,
        vector_chunks: vectorResult.chunks.length,
        graph_triplets: graphResult.triplets.length,
        fusion_score: fusionScore
      });
      
      return context;
    } catch (error) {
      this.emit('error', {
        operation: 'merge_context',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Calculate average vector score
   */
  private calculateVectorScore(result: RetrievalResult): number {
    if (result.relevance_scores.length === 0) return 0;
    return result.relevance_scores.reduce((sum, score) => sum + score, 0) / 
           result.relevance_scores.length;
  }

  /**
   * Calculate average graph score
   */
  private calculateGraphScore(result: GraphRetrievalResult): number {
    if (result.triplets.length === 0) return 0;
    const scores = result.triplets.map(t => t.metadata.confidence);
    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
  }

  /**
   * Reciprocal Rank Fusion (RRF)
   */
  private reciprocalRankFusion(vectorScore: number, graphScore: number): number {
    const k = 60; // RRF constant
    const vectorRank = 1 / (k + (1 - vectorScore) * 100);
    const graphRank = 1 / (k + (1 - graphScore) * 100);
    return (vectorRank + graphRank) / 2;
  }

  /**
   * Cascade fusion - use graph only if vector score is low
   */
  private cascadeFusion(vectorScore: number, graphScore: number): number {
    const threshold = 0.7;
    if (vectorScore >= threshold) {
      return vectorScore;
    }
    return Math.max(vectorScore, graphScore);
  }

  /**
   * Build merged context from chunks and triplets
   */
  private buildMergedContext(
    chunks: VectorChunk[],
    triplets: KnowledgeTriplet[]
  ): string {
    const sections: string[] = [];
    
    // Add vector context
    if (chunks.length > 0) {
      sections.push('## Vector Context\n');
      chunks.forEach((chunk, i) => {
        sections.push(`[${i + 1}] ${chunk.content}\n`);
      });
    }
    
    // Add graph context
    if (triplets.length > 0) {
      sections.push('\n## Knowledge Graph Context\n');
      triplets.forEach((triplet, i) => {
        sections.push(
          `[${i + 1}] ${triplet.subject} ${triplet.predicate} ${triplet.object}\n`
        );
      });
    }
    
    return sections.join('');
  }

  /**
   * Automatic context assembly for generation
   */
  async assembleContext(
    query: string,
    config?: Partial<HybridQueryConfig>
  ): Promise<string> {
    try {
      const result = await this.query({
        query,
        ...config
      } as HybridQueryConfig);
      
      return result.context.merged_context;
    } catch (error) {
      this.emit('error', {
        operation: 'assemble_context',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Faithfulness verification - check if answer is grounded in context
   */
  async verifyFaithfulness(
    answer: string,
    context: HybridContext
  ): Promise<{
    faithful: boolean;
    score: number;
    evidence: string[];
  }> {
    try {
      const evidence: string[] = [];
      let matchCount = 0;
      
      // Check against vector chunks
      for (const chunk of context.vector_chunks) {
        if (this.containsEvidence(answer, chunk.content)) {
          evidence.push(chunk.content);
          matchCount++;
        }
      }
      
      // Check against triplets
      for (const triplet of context.knowledge_triplets) {
        const tripletText = `${triplet.subject} ${triplet.predicate} ${triplet.object}`;
        if (this.containsEvidence(answer, tripletText)) {
          evidence.push(tripletText);
          matchCount++;
        }
      }
      
      const totalContext = context.vector_chunks.length + context.knowledge_triplets.length;
      const score = totalContext > 0 ? matchCount / totalContext : 0;
      const faithful = score > 0.3; // Threshold for faithfulness
      
      this.emit('faithfulness_verified', {
        answer_length: answer.length,
        evidence_count: evidence.length,
        score,
        faithful
      });
      
      return { faithful, score, evidence };
    } catch (error) {
      this.emit('error', {
        operation: 'verify_faithfulness',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Check if answer contains evidence from context
   */
  private containsEvidence(answer: string, context: string): boolean {
    const answerWords = new Set(answer.toLowerCase().split(/\s+/));
    const contextWords = context.toLowerCase().split(/\s+/);
    
    let matchCount = 0;
    for (const word of contextWords) {
      if (answerWords.has(word) && word.length > 3) {
        matchCount++;
      }
    }
    
    return matchCount >= 3; // At least 3 matching words
  }

  /**
   * Answer relevance scoring
   */
  async scoreAnswerRelevance(
    answer: string,
    query: string
  ): Promise<number> {
    try {
      // Simple word overlap scoring (in production, use semantic similarity)
      const answerWords = new Set(answer.toLowerCase().split(/\s+/));
      const queryWords = query.toLowerCase().split(/\s+/);
      
      let matchCount = 0;
      for (const word of queryWords) {
        if (answerWords.has(word) && word.length > 3) {
          matchCount++;
        }
      }
      
      const score = queryWords.length > 0 ? matchCount / queryWords.length : 0;
      
      this.emit('answer_relevance_scored', {
        query,
        answer_length: answer.length,
        score
      });
      
      return score;
    } catch (error) {
      this.emit('error', {
        operation: 'score_answer_relevance',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Get statistics
   */
  getStats(): {
    vector_stats: any;
    graph_stats: any;
  } {
    return {
      vector_stats: this.vectorRAG.getStats(),
      graph_stats: this.graphRAG.getStats()
    };
  }

  /**
   * Clear all data
   */
  clear(): void {
    this.vectorRAG.clear();
    this.graphRAG.clear();
    this.emit('cleared');
  }
}

/**
 * Factory function to create HybridRAG instance
 */
export function createHybridRAG(vectorRAG: VectorRAG, graphRAG: GraphRAG): HybridRAG {
  return new HybridRAG(vectorRAG, graphRAG);
}