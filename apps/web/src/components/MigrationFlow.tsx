/**
 * @fileoverview Migration flow visualization component using Mermaid Sankey diagrams.
 *
 * This component visualizes language/technology migration patterns showing the flow
 * of migrations from source technologies to target technologies, distinguishing
 * between historical (completed) and suggested migrations.
 *
 * @module components/MigrationFlow
 */

import Mermaid from './Mermaid';

/**
 * Represents a single migration path between two technologies.
 *
 * @interface MigrationEdge
 * @property {string} source - Source technology/language being migrated from
 * @property {string} target - Target technology/language being migrated to
 * @property {number} count - Number of migrations along this path
 * @property {'history' | 'suggested'} type - Whether this is a historical or suggested migration
 */
interface MigrationEdge {
  source: string;
  target: string;
  count: number;
  type: 'history' | 'suggested';
}

/**
 * Props for the MigrationFlow component.
 *
 * @interface MigrationFlowProps
 * @property {MigrationEdge[]} edges - Array of migration paths to visualize
 * @property {Object} [statistics] - Optional aggregate statistics about migrations
 */
interface MigrationFlowProps {
  edges: MigrationEdge[];
  statistics?: {
    totalMigrations: number;
    historicalMigrations: number;
    suggestedMigrations: number;
    mostCommonSource: string;
    mostCommonTarget: string;
  };
}

/**
 * Migration flow visualization component displaying Sankey diagrams and statistics.
 *
 * This component renders:
 * 1. **Sankey Diagram**: Visual flow chart showing migration paths using Mermaid
 * 2. **Statistics Cards**: Summary metrics (total, historical, suggested migrations)
 * 3. **Migration Table**: Top 10 migration paths with details
 * 4. **Legend**: Explanation of historical vs suggested migration indicators
 *
 * Features:
 * - Dark theme styling consistent with the application design
 * - Color-coded migration types (green for historical, blue for suggested)
 * - Responsive grid layout for statistics cards
 * - Fallback display when no migration data is available
 *
 * @param props - Component props
 * @param props.edges - Array of migration edges to display
 * @param props.statistics - Optional statistics object for summary cards
 * @returns The rendered MigrationFlow component
 *
 * @example
 * // Basic usage with edges
 * <MigrationFlow
 *   edges={[
 *     { source: 'JavaScript', target: 'TypeScript', count: 15, type: 'history' },
 *     { source: 'Java', target: 'Kotlin', count: 8, type: 'suggested' }
 *   ]}
 * />
 *
 * @example
 * // With statistics
 * <MigrationFlow
 *   edges={edges}
 *   statistics={{
 *     totalMigrations: 100,
 *     historicalMigrations: 75,
 *     suggestedMigrations: 25,
 *     mostCommonSource: 'JavaScript',
 *     mostCommonTarget: 'TypeScript'
 *   }}
 * />
 */
export default function MigrationFlow({ edges, statistics }: MigrationFlowProps) {
  /**
   * Generates a Mermaid Sankey diagram definition from migration edges.
   *
   * Converts the edges array into Mermaid sankey-beta format with dark theme.
   * Returns a simple flowchart with "No Migration Data" if edges array is empty.
   *
   * @returns Mermaid diagram definition string
   */
  const generateSankeyDiagram = (): string => {
    if (edges.length === 0) {
      return `
flowchart LR
  A[No Migration Data]
      `;
    }

    // Build sankey diagram
    const lines = ['%%{init: {"theme": "dark"}}%%', 'sankey-beta', ''];
    
    edges.forEach(edge => {
      // Format: Source,Target,Value
      lines.push(`${edge.source},${edge.target},${edge.count}`);
    });

    return lines.join('\n');
  };

  /**
   * Returns the Tailwind CSS color class for a migration type.
   *
   * @param type - The migration type ('history' or 'suggested')
   * @returns Tailwind text color class string
   */
  const getTypeColor = (type: string): string => {
    return type === 'history' ? 'text-green-500' : 'text-blue-500';
  };

  /**
   * Returns the display icon for a migration type.
   *
   * @param type - The migration type ('history' or 'suggested')
   * @returns Icon character (✓ for history, → for suggested)
   */
  const getTypeIcon = (type: string): string => {
    return type === 'history' ? '✓' : '→';
  };

  return (
    <div className="space-y-6">
      {/* Mermaid Sankey Diagram */}
      <div className="bg-slate-900/50 rounded-lg p-6">
        <Mermaid chart={generateSankeyDiagram()} />
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <div className="text-sm text-slate-400 mb-1">Total Migrations</div>
            <div className="text-2xl font-bold text-slate-200">
              {statistics.totalMigrations}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Historical: {statistics.historicalMigrations} | Suggested: {statistics.suggestedMigrations}
            </div>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <div className="text-sm text-slate-400 mb-1">Most Common Source</div>
            <div className="text-lg font-semibold text-slate-200 font-mono">
              {statistics.mostCommonSource}
            </div>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <div className="text-sm text-slate-400 mb-1">Most Common Target</div>
            <div className="text-lg font-semibold text-slate-200 font-mono">
              {statistics.mostCommonTarget}
            </div>
          </div>
        </div>
      )}

      {/* Migration Edges Table */}
      <div className="bg-slate-900/30 rounded-lg p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">
          Top Migration Paths
        </h3>
        <div className="space-y-2">
          {edges.slice(0, 10).map((edge, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3 flex-1">
                <span className={`text-lg ${getTypeColor(edge.type)}`}>
                  {getTypeIcon(edge.type)}
                </span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-blue-400">{edge.source}</span>
                  <span className="text-slate-500">→</span>
                  <span className="font-mono text-green-400">{edge.target}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-slate-400">{edge.count}</span>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    edge.type === 'history'
                      ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                      : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                  }`}
                >
                  {edge.type}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm text-slate-400">
        <div className="flex items-center gap-2">
          <span className="text-green-500">✓</span>
          <span>Historical (completed migrations)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-blue-500">→</span>
          <span>Suggested (based on violations)</span>
        </div>
      </div>
    </div>
  );
}
