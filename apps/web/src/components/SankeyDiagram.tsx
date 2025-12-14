/**
 * @fileoverview Sankey diagram component for visualizing code violation flows.
 *
 * This component creates multi-level Sankey diagrams showing the flow from
 * source layers through languages to violation types and fix targets.
 * Uses Mermaid.js for rendering with strict security settings.
 *
 * @module components/SankeyDiagram
 */

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

/**
 * Data structure for a single node in the Sankey diagram flow.
 *
 * Represents the path: sourceLayer → language → violationType → fixTarget
 *
 * @interface SankeyNode
 * @property {string} sourceLayer - The architectural layer where the issue originated
 * @property {string} language - The programming language involved
 * @property {string} violationType - The type of code violation detected
 * @property {string} fixTarget - The recommended fix or target state
 * @property {number} [count] - Optional weight/count for this flow (defaults to 1)
 */
interface SankeyNode {
  sourceLayer: string;
  language: string;
  violationType: string;
  fixTarget: string;
  count?: number;
}

/**
 * Props for the SankeyDiagram component.
 *
 * @interface SankeyDiagramProps
 * @property {SankeyNode[]} data - Array of nodes defining the diagram flows
 */
interface SankeyDiagramProps {
  data: SankeyNode[];
}

/**
 * Sankey diagram visualization component for code violation flows.
 *
 * Renders a multi-level Sankey diagram showing how code issues flow through
 * the system: from source layers → languages → violation types → fix targets.
 *
 * Features:
 * - **Security**: Uses mermaid.render with cryptographically secure unique IDs when available, with a timestamp-based fallback if necessary
 * - **XSS Prevention**: All user inputs are sanitized before rendering
 * - **Dark Theme**: Custom dark theme variables matching application design
 * - **Error Handling**: Graceful fallback message on render errors
 * - **Responsive**: Horizontal scrolling for wide diagrams
 *
 * @param props - Component props
 * @param props.data - Array of SankeyNode objects defining the flows
 * @returns The rendered SankeyDiagram component
 *
 * @example
 * <SankeyDiagram
 *   data={[
 *     {
 *       sourceLayer: 'Frontend',
 *       language: 'TypeScript',
 *       violationType: 'Type Error',
 *       fixTarget: 'Add Type Annotation',
 *       count: 5
 *     }
 *   ]}
 * />
 */
export default function SankeyDiagram({ data }: SankeyDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current && data.length > 0) {
      // Generate Sankey diagram from data
      const sankeyChart = generateSankeyChart(data);
      // Security: Use mermaid.render for safer rendering with cryptographically secure IDs
      // Use crypto.randomUUID() if available, fallback to timestamp-based ID
      const uniqueId = typeof crypto !== 'undefined' && crypto.randomUUID 
        ? crypto.randomUUID() 
        : `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
      const id = `sankey-${uniqueId}`;
      
      mermaid.render(id, sankeyChart).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      }).catch(err => {
        console.error('Sankey diagram rendering error:', err);
        if (ref.current) {
          ref.current.textContent = 'Error rendering diagram';
        }
      });
    }
  }, [data]);

  return (
    <div className="w-full overflow-x-auto">
      <div ref={ref} className="mermaid min-w-[600px]" />
    </div>
  );
}

/**
 * Sanitizes a string for safe inclusion in Mermaid diagram definitions.
 *
 * Performs HTML entity encoding and removes characters that could break
 * Mermaid syntax or enable XSS attacks. Applied to all user-provided strings
 * before including them in the diagram.
 *
 * Security measures:
 * - Encodes HTML entities (&, <, >, ", ')
 * - Removes line breaks and tabs (prevent syntax injection)
 * - Replaces brackets that affect Mermaid parsing
 *
 * @param str - The raw string to sanitize
 * @returns The sanitized string safe for Mermaid diagram inclusion
 *
 * @example
 * sanitizeString('<script>alert("xss")</script>')
 * // Returns: '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
 *
 * @security Prevents XSS through Mermaid diagram injection
 */
function sanitizeString(str: string): string {
  // Security: Escape dangerous characters while preserving valid Mermaid syntax
  // Handle ampersands first to avoid double-encoding, then escape other dangerous characters
  return String(str)
    .replace(/&/g, '&amp;')  // Must be first to avoid double-encoding
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    // Remove any Mermaid-specific syntax that could break diagram structure
    .replace(/[\n\r\t]/g, ' ')  // Remove line breaks and tabs
    .replace(/[{}[\]]/g, '_');  // Remove curly braces and brackets that affect Mermaid syntax
}

/**
 * Generates a complete Mermaid Sankey chart definition from node data.
 *
 * Creates a multi-level flow showing:
 * sourceLayer → language → violationType → fixTarget
 *
 * Each node in the data array creates three flow connections with the
 * specified count (defaulting to 1).
 *
 * @param data - Array of SankeyNode objects to include in the chart
 * @returns Complete Mermaid sankey-beta definition string with dark theme
 *
 * @example
 * const chart = generateSankeyChart([
 *   { sourceLayer: 'API', language: 'Go', violationType: 'Error', fixTarget: 'Fix' }
 * ]);
 * // Returns Mermaid sankey definition with flows: API→Go, Go→Error, Error→Fix
 */
function generateSankeyChart(data: SankeyNode[]): string {
  // Group by source layer, language, and fix target
  const flows = data.map(node => {
    const count = node.count || 1;
    // Security: Sanitize all user-provided strings to prevent XSS
    // Note: Mermaid with strict security level provides additional protection
    const source = sanitizeString(node.sourceLayer);
    const language = sanitizeString(node.language);
    const violation = sanitizeString(node.violationType);
    const target = sanitizeString(node.fixTarget);
    
    return `${source},${language},${count}\n${language},${violation},${count}\n${violation},${target},${count}`;
  }).join('\n');

  return `
%%{init: {'theme':'dark', 'themeVariables': { 'primaryColor': '#3b82f6', 'primaryTextColor': '#fff', 'primaryBorderColor': '#1e40af', 'lineColor': '#64748b', 'secondaryColor': '#1e293b', 'tertiaryColor': '#0f172a'}}}%%
sankey-beta

${flows}
  `.trim();
}
