/**
 * Oracle visual layer — types.
 *
 * These augment the existing TranscriptEvent contract. The Oracle subscribes
 * to the same SSE stream as /live, so no new backend event schema is required.
 */

export type OracleStatus = 'idle' | 'listening' | 'speaking' | 'blocked' | 'error';

export interface OracleImageResponse {
  status: 'ok' | 'blocked' | 'error';
  image?: string;           // data URL, full-bleed background
  visual_prompt?: string;   // the distilled image prompt (hidden in debug mode)
  reason?: string;          // block reason when status === 'blocked'
  error?: string;
}

export interface OracleScene {
  /** Unique id for cross-fade bookkeeping. */
  id: string;
  /** The agent reply text shown as typography overlay. */
  agentText: string;
  /** Data URL of the generated image, or null when still loading / blocked. */
  imageUrl: string | null;
  /** Set when content policy fired. */
  blocked: boolean;
  blockReason?: string;
  /** True while the image is generating. */
  loading: boolean;
  /** Timestamp the scene became active. */
  enteredAt: number;
}
