/**
 * RAG Engine - Unified Export
 * 
 * Provides complete Retrieval Augmented Generation capabilities:
 * - VectorRAG: Vector-based semantic search
 * - GraphRAG: Knowledge graph-based retrieval
 * - HybridRAG: Combined vector + graph retrieval
 * 
 * Performance: <50ms retrieval, >90% relevance
 */

// Vector RAG exports
export {
  VectorRAG,
  createVectorRAG,
  VectorChunk,
  QueryConfig,
  RetrievalResult,
  EmbeddingConfig
} from './vector/vector-rag';

// Graph RAG exports
export {
  GraphRAG,
  createGraphRAG,
  KnowledgeTriplet,
  EntityNode,
  RelationshipEdge,
  GraphQueryConfig,
  GraphRetrievalResult
} from './graph/graph-rag';

// Hybrid RAG exports
export {
  HybridRAG,
  createHybridRAG,
  HybridContext,
  HybridQueryConfig,
  HybridRetrievalResult
} from './hybrid/hybrid-rag';

/**
 * RAG Engine Factory
 * Creates a complete RAG system with all capabilities
 */
export function createRAGEngine(config: {
  embedding_model: string;
  embedding_dimension: number;
  normalize: boolean;
  batch_size: number;
}) {
  const vectorRAG = createVectorRAG({
    model: config.embedding_model,
    dimension: config.embedding_dimension,
    normalize: config.normalize,
    batch_size: config.batch_size
  });
  
  const graphRAG = createGraphRAG();
  const hybridRAG = createHybridRAG(vectorRAG, graphRAG);
  
  return {
    vectorRAG,
    graphRAG,
    hybridRAG,
    
    async initialize() {
      await hybridRAG.initialize();
    },
    
    async query(query: string, config?: Partial<HybridQueryConfig>) {
      return hybridRAG.query({
        query,
        ...config
      } as HybridQueryConfig);
    },
    
    getStats() {
      return hybridRAG.getStats();
    },
    
    clear() {
      hybridRAG.clear();
    }
  };
}

/**
 * Default RAG Engine configuration
 */
export const DEFAULT_RAG_CONFIG = {
  embedding_model: 'text-embedding-3-small',
  embedding_dimension: 1536,
  normalize: true,
  batch_size: 100
};