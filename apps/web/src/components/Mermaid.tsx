/**
 * @fileoverview Mermaid diagram rendering component with secure configuration.
 *
 * This component provides a React wrapper for Mermaid.js diagram rendering,
 * configured with strict security settings and a dark theme matching the
 * application design.
 *
 * @module components/Mermaid
 */

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

/**
 * Initialize Mermaid.js with secure settings and custom dark theme.
 *
 * Configuration:
 * - startOnLoad: true - Auto-renders on DOM ready
 * - theme: 'dark' - Uses dark color scheme
 * - securityLevel: 'strict' - Prevents XSS through diagram content
 *
 * Theme variables are customized to match the application's Tailwind CSS
 * color palette (slate and blue tones).
 *
 * @security securityLevel is set to 'strict' to prevent XSS attacks
 * through malicious diagram definitions.
 */
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'strict', // Security: Changed from 'loose' to 'strict' to prevent XSS
  themeVariables: {
    primaryColor: '#3b82f6',
    primaryTextColor: '#fff',
    primaryBorderColor: '#1e40af',
    lineColor: '#64748b',
    secondaryColor: '#1e293b',
    tertiaryColor: '#0f172a',
  },
});

/**
 * Props for the Mermaid component.
 *
 * @interface MermaidProps
 * @property {string} chart - Mermaid diagram definition string
 */
interface MermaidProps {
  chart: string;
}

/**
 * React component for rendering Mermaid diagrams securely.
 *
 * This component accepts a Mermaid diagram definition string and renders
 * it as SVG using Mermaid.js. It handles:
 * - Secure rendering with cryptographically random element IDs
 * - Automatic re-rendering when the chart prop changes
 * - Error handling with fallback message display
 *
 * Security Features:
 * - Uses crypto.randomUUID() for unique IDs (prevents ID collision attacks)
 * - Falls back to timestamp-based IDs if crypto API unavailable
 * - Strict security level prevents script execution in diagrams
 *
 * @param props - Component props
 * @param props.chart - Mermaid diagram definition string
 * @returns The rendered Mermaid component with SVG output
 *
 * @example
 * // Simple flowchart
 * <Mermaid chart="flowchart LR\n  A --> B --> C" />
 *
 * @example
 * // Sequence diagram
 * <Mermaid chart={`
 *   sequenceDiagram
 *     Alice->>Bob: Hello
 *     Bob-->>Alice: Hi!
 * `} />
 *
 * @example
 * // Sankey diagram (beta)
 * <Mermaid chart={`
 *   sankey-beta
 *   Source,Target,10
 * `} />
 */
export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      // Security: Use mermaid.render with strict security level for safe rendering
      // The strict security level handles sanitization internally
      // Use crypto.randomUUID() if available, fallback to timestamp-based ID
      const uniqueId = typeof crypto !== 'undefined' && crypto.randomUUID 
        ? crypto.randomUUID() 
        : `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
      const id = `mermaid-${uniqueId}`;
      
      mermaid.render(id, chart).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      }).catch(err => {
        console.error('Mermaid rendering error:', err);
        if (ref.current) {
          ref.current.textContent = 'Error rendering diagram';
        }
      });
    }
  }, [chart]);

  return <div ref={ref} className="mermaid" />;
}
