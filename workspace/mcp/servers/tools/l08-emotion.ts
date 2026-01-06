/**
 * Layer L08: Emotional Intelligence Tools
 * Emotion classification, tone adjustment, empathy modeling
 * @module tools/l08-emotion
 */

import type { ToolDefinition } from "./types.js";

export const L08_TOOLS: ToolDefinition[] = [
  {
    name: "emotion_content",
    description: "BERT-based emotion classification with Plutchik model",
    source_module: "AXM-L08-EMOT-001",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        classification_model: { type: "string", enum: ["plutchik", "ekman", "dimensional", "custom"] },
        granularity: { type: "string", enum: ["coarse", "fine", "ultra_fine"] },
      },
      required: ["text"],
    },
    quantum_enabled: true,
    priority: 27,
  },
  {
    name: "tone_adjuster",
    description: "Neural tone transformation with style transfer",
    source_module: "AXM-L08-TONE-002",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        target_tone: {
          type: "string",
          enum: ["formal", "informal", "friendly", "professional", "empathetic", "assertive"],
        },
        target_formality: { type: "number", default: 0.5 },
        preserve_meaning: { type: "boolean", default: true },
      },
      required: ["text", "target_tone"],
    },
    quantum_enabled: false,
    priority: 28,
  },
  {
    name: "empathy_engine",
    description: "Computational empathy with Theory of Mind",
    source_module: "AXM-L08-EMPA-003",
    input_schema: {
      type: "object",
      properties: {
        context: { type: "object" },
        user_state: { type: "object" },
        response_type: {
          type: "string",
          enum: ["supportive", "informative", "action_oriented", "reflective"],
        },
      },
      required: ["context"],
    },
    quantum_enabled: false,
    priority: 29,
  },
];
