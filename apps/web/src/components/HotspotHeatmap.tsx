/**
 * @fileoverview Treemap-style heatmap component for visualizing code hotspots.
 *
 * This component renders a canvas-based treemap visualization showing files
 * with code quality issues, using color intensity to represent severity scores.
 *
 * @module components/HotspotHeatmap
 */

import { useEffect, useRef } from 'react';

/**
 * Data structure representing a code hotspot (file with quality issues).
 *
 * @interface HotspotData
 * @property {string} file - Full path to the file
 * @property {string} layer - Architectural layer (e.g., 'Frontend', 'Backend')
 * @property {string} language - Programming language of the file
 * @property {string[]} violations - Array of violation type identifiers
 * @property {number} security_issues - Count of security-related issues
 * @property {number} repeated_count - Number of times violations have occurred
 * @property {number} score - Aggregate severity score (0-100)
 */
interface HotspotData {
  file: string;
  layer: string;
  language: string;
  violations: string[];
  security_issues: number;
  repeated_count: number;
  score: number;
}

/**
 * Props for the HotspotHeatmap component.
 *
 * @interface HotspotHeatmapProps
 * @property {HotspotData[]} hotspots - Array of hotspot data to visualize
 */
interface HotspotHeatmapProps {
  hotspots: HotspotData[];
}

/**
 * Canvas-based treemap heatmap component for code hotspot visualization.
 *
 * Renders a treemap where:
 * - Rectangle size is proportional to the hotspot's severity score
 * - Rectangle color indicates severity level (red = critical, amber = moderate)
 * - File names and scores are displayed on sufficiently large rectangles
 *
 * Color Legend (as displayed in UI):
 * - Red (#dc2626): Critical (score 70-100)
 * - Amber (#f59e0b): High (score 40-69)
 * - Yellow (#fbbf24): Moderate (score 1-39)
 *   (Moderate and Low are combined in the visual legend)
 *
 * Features:
 * - Canvas-based rendering for performance with many hotspots
 * - Responsive width with fixed 400px height
 * - Squarified treemap algorithm for optimal rectangle proportions
 * - Auto-truncation of long file names
 * - Color-coded legend below the visualization
 *
 * @param props - Component props
 * @param props.hotspots - Array of hotspot data to display
 * @returns The rendered HotspotHeatmap component
 *
 * @example
 * <HotspotHeatmap
 *   hotspots={[
 *     {
 *       file: 'src/components/Form.tsx',
 *       layer: 'Frontend',
 *       language: 'TypeScript',
 *       violations: ['type-error', 'unused-var'],
 *       security_issues: 0,
 *       repeated_count: 3,
 *       score: 45
 *     }
 *   ]}
 * />
 */
export default function HotspotHeatmap({ hotspots }: HotspotHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || hotspots.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const width = canvas.clientWidth;
    const height = 400;
    canvas.width = width;
    canvas.height = height;

    // Calculate treemap layout
    const layout = calculateTreemap(hotspots, width, height);

    // Draw heatmap
    layout.forEach((rect, index) => {
      const hotspot = hotspots[index];
      const color = getHeatColor(hotspot.score);

      // Draw rectangle
      ctx.fillStyle = color;
      ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

      // Draw border
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 2;
      ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);

      // Draw text if rectangle is large enough
      if (rect.width > 80 && rect.height > 40) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const fileName = hotspot.file.split('/').pop() || hotspot.file;
        const text = `${fileName.substring(0, 15)}${fileName.length > 15 ? '...' : ''}`;
        ctx.fillText(text, rect.x + rect.width / 2, rect.y + rect.height / 2 - 10);

        ctx.font = 'bold 16px sans-serif';
        ctx.fillText(`${hotspot.score}`, rect.x + rect.width / 2, rect.y + rect.height / 2 + 10);
      }
    });
  }, [hotspots]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="w-full rounded-lg"
        style={{ height: '400px' }}
      />
      <div className="mt-4 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#dc2626' }} />
            <span className="text-slate-400">Critical (70-100)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }} />
            <span className="text-slate-400">High (40-69)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#fbbf24' }} />
            <span className="text-slate-400">Moderate (1-39)</span>
          </div>
        </div>
        <div className="text-slate-500">
          Hover over blocks for details
        </div>
      </div>
    </div>
  );
}

/**
 * Maps a severity score to a heat color for the treemap visualization.
 *
 * Color scale:
 * - Critical (70-100): Red (#dc2626) - Tailwind red-600
 * - High (40-69): Orange (#f59e0b) - Tailwind amber-500
 * - Moderate (20-39): Yellow (#fbbf24) - Tailwind amber-400
 * - Low (0-19): Light yellow (#fcd34d) - Tailwind amber-300
 *
 * @param score - Severity score from 0-100
 * @returns Hex color string for the given score
 *
 * @example
 * getHeatColor(85);  // Returns '#dc2626' (critical - red)
 * getHeatColor(50);  // Returns '#f59e0b' (high - orange)
 * getHeatColor(25);  // Returns '#fbbf24' (moderate - yellow)
 * getHeatColor(10);  // Returns '#fcd34d' (low - light yellow)
 */
function getHeatColor(score: number): string {
  if (score >= 70) return '#dc2626'; // red-600
  if (score >= 40) return '#f59e0b'; // amber-500
  if (score >= 20) return '#fbbf24'; // amber-400
  return '#fcd34d'; // amber-300
}

/**
 * Calculates a squarified treemap layout for the given hotspots.
 *
 * Uses a simplified squarified treemap algorithm that alternates between
 * horizontal and vertical splits to create rectangles proportional to each
 * hotspot's score relative to the total.
 *
 * Algorithm:
 * 1. Calculate total score sum for proportional sizing
 * 2. For each hotspot, calculate area based on score ratio
 * 3. Alternate between horizontal and vertical placement
 * 4. Enforce minimum dimensions (40px) for visibility
 *
 * @param hotspots - Array of hotspot data with scores
 * @param width - Total width of the treemap area
 * @param height - Total height of the treemap area
 * @returns Array of rectangle coordinates and dimensions
 *
 * @example
 * const layout = calculateTreemap(hotspots, 800, 400);
 * // Returns: [{ x: 0, y: 0, width: 200, height: 400 }, ...]
 */
function calculateTreemap(
  hotspots: HotspotData[],
  width: number,
  height: number
): Array<{ x: number; y: number; width: number; height: number }> {
  // Simple squarified treemap algorithm
  const totalScore = hotspots.reduce((sum, h) => sum + h.score, 0);
  const rects: Array<{ x: number; y: number; width: number; height: number }> = [];

  let x = 0;
  let y = 0;
  let remainingWidth = width;
  let remainingHeight = height;

  hotspots.forEach((hotspot, index) => {
    const ratio = hotspot.score / totalScore;
    const area = width * height * ratio;

    let rectWidth: number;
    let rectHeight: number;

    // Alternate between horizontal and vertical splits
    if (index % 2 === 0) {
      rectWidth = Math.min(remainingWidth, Math.sqrt(area * (remainingWidth / remainingHeight)));
      rectHeight = area / rectWidth;
    } else {
      rectHeight = Math.min(remainingHeight, Math.sqrt(area * (remainingHeight / remainingWidth)));
      rectWidth = area / rectHeight;
    }

    rects.push({
      x: x,
      y: y,
      width: Math.max(40, rectWidth), // Minimum width
      height: Math.max(40, rectHeight), // Minimum height
    });

    // Update position for next rectangle
    if (index % 2 === 0) {
      x += rectWidth;
      remainingWidth -= rectWidth;
    } else {
      y += rectHeight;
      remainingHeight -= rectHeight;
    }
  });

  return rects;
}
