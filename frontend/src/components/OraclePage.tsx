/**
 * OraclePage — the fullscreen immersive visual layer for the 47 DOORS
 * voice agent. Projected to the audience at NYU ITP/IMA (April 23, 2026).
 *
 * Subscribes to the phone transcript SSE stream and, for every agent reply,
 * conjures a cinematic image via Azure OpenAI Images. The "BLOCKED" state
 * visualizes Azure Content Safety firing — the visible absence of art IS
 * the ethics lesson.
 *
 * Mount at route `/oracle`. Projector-safe: dark defaults, no chrome.
 */

import { useEffect, useState } from 'react';
import { useOracle } from '../hooks/useOracle';

const PHONE_NUMBER = '+1 (913) 217-1946';

// ─── Ambient background (when no image yet) ──────────────────────────────────

function AmbientField() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Deep gradient */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse at 30% 40%, #2a1f3d 0%, #0d0a14 55%, #030206 100%)',
        }}
      />
      {/* Slow drifting nebula */}
      <div
        className="absolute -inset-[20%] opacity-40 animate-oracle-drift"
        style={{
          background:
            'radial-gradient(circle at 20% 30%, #b8935a 0%, transparent 40%),' +
            'radial-gradient(circle at 80% 70%, #4a3a7d 0%, transparent 45%),' +
            'radial-gradient(circle at 50% 90%, #7d3a3a 0%, transparent 40%)',
          filter: 'blur(60px)',
        }}
      />
      {/* Grain overlay */}
      <div
        className="absolute inset-0 opacity-[0.08] mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage:
            'url("data:image/svg+xml;utf8,' +
            "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'>" +
            "<filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='3'/></filter>" +
            "<rect width='100%' height='100%' filter='url(%23n)'/></svg>" +
            '")',
        }}
      />
    </div>
  );
}

// ─── Scene layer: the generated image ────────────────────────────────────────

function SceneLayer({
  src,
  isCurrent,
  blocked,
}: {
  src: string | null;
  isCurrent: boolean;
  blocked: boolean;
}) {
  if (!src || blocked) return null;
  return (
    <div
      className={`absolute inset-0 transition-opacity duration-[1800ms] ease-out ${
        isCurrent ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <img
        src={src}
        alt=""
        className="absolute inset-0 w-full h-full object-cover"
        style={{ filter: 'saturate(1.05) contrast(1.03)' }}
      />
      {/* Dark vignette + bottom gradient for text legibility */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-black/50" />
      <div className="absolute inset-0 shadow-[inset_0_0_300px_rgba(0,0,0,0.7)]" />
    </div>
  );
}

// ─── The BLOCKED state — the ethics money shot ───────────────────────────────

function BlockedLayer({ reason }: { reason: string | undefined }) {
  return (
    <div className="absolute inset-0 animate-oracle-block-in">
      {/* Crimson field */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse at center, #7a0d0d 0%, #3a0404 60%, #0a0000 100%)',
        }}
      />
      {/* Scan lines */}
      <div
        className="absolute inset-0 opacity-30 mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 3px)',
        }}
      />
      <div className="relative h-full w-full flex flex-col items-center justify-center px-16">
        <div
          className="text-[14vw] leading-none font-black tracking-tight text-white/95 select-none"
          style={{
            fontFamily: '"JetBrains Mono", monospace',
            letterSpacing: '-0.04em',
            textShadow: '0 0 40px rgba(255,50,50,0.4)',
          }}
        >
          BLOCKED
        </div>
        <div className="mt-8 max-w-3xl text-center">
          <div
            className="text-xs uppercase tracking-[0.4em] text-red-300/70 mb-4"
            style={{ fontFamily: '"JetBrains Mono", monospace' }}
          >
            Azure Content Safety · guardrail fired
          </div>
          <div
            className="text-2xl text-white/90 leading-relaxed"
            style={{ fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic' }}
          >
            {reason || 'The system declined to generate imagery for this response.'}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Typography overlay (user utterance + agent reply) ───────────────────────

function UserWhisper({ text }: { text: string }) {
  return (
    <div
      key={text}
      className="absolute top-[12vh] left-1/2 -translate-x-1/2 max-w-[80vw] text-center animate-oracle-whisper"
    >
      <div
        className="text-xs uppercase tracking-[0.5em] text-white/40 mb-3"
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
      >
        You ask
      </div>
      <div
        className="text-3xl md:text-4xl text-white/85 leading-tight italic"
        style={{ fontFamily: '"Cormorant Garamond", serif' }}
      >
        "{text}"
      </div>
    </div>
  );
}

function AgentReply({ text, loading }: { text: string; loading: boolean }) {
  return (
    <div className="absolute bottom-[10vh] left-1/2 -translate-x-1/2 max-w-[78vw] text-center">
      <div
        className="text-xs uppercase tracking-[0.5em] text-amber-200/60 mb-4 animate-oracle-pulse"
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
      >
        {loading ? 'The Oracle conjures' : 'The Oracle answers'}
      </div>
      <div
        key={text}
        className="text-3xl md:text-[2.6rem] leading-[1.2] text-white animate-oracle-reveal"
        style={{
          fontFamily: '"Cormorant Garamond", serif',
          textShadow: '0 2px 20px rgba(0,0,0,0.9), 0 0 80px rgba(0,0,0,0.4)',
        }}
      >
        {text}
      </div>
    </div>
  );
}

// ─── Idle state (waiting for a call) ─────────────────────────────────────────

function IdlePanel() {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    const t = setInterval(() => setPulse((p) => !p), 2200);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center px-8">
      <div
        className="text-xs uppercase tracking-[0.6em] text-amber-200/60 mb-8"
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
      >
        47 Doors · the Oracle
      </div>
      <div
        className="text-[9vw] leading-[0.95] text-center text-white/95 mb-10"
        style={{
          fontFamily: '"Cormorant Garamond", serif',
          fontWeight: 300,
          letterSpacing: '-0.02em',
        }}
      >
        Ask, and the<br />
        <span className="italic text-amber-100/90">vision answers.</span>
      </div>
      <div
        className={`flex items-center gap-4 px-6 py-3 rounded-full border border-amber-200/20 bg-black/30 backdrop-blur-sm transition-opacity duration-[1400ms] ${
          pulse ? 'opacity-100' : 'opacity-60'
        }`}
      >
        <span className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400/50 animate-ping" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-400" />
        </span>
        <span
          className="text-base tracking-[0.2em] text-white/80"
          style={{ fontFamily: '"JetBrains Mono", monospace' }}
        >
          {PHONE_NUMBER}
        </span>
      </div>
      <div
        className="mt-6 text-sm text-white/40 tracking-wider"
        style={{ fontFamily: '"Cormorant Garamond", serif', fontStyle: 'italic' }}
      >
        call to speak with her
      </div>
    </div>
  );
}

// ─── Stat strip (bottom-left, tiny, for presenters) ──────────────────────────

function StatStrip({
  responses,
  blocked,
  toolHint,
}: {
  responses: number;
  blocked: number;
  toolHint: string | null;
}) {
  return (
    <div
      className="absolute bottom-4 left-6 flex items-center gap-6 text-[10px] tracking-[0.3em] uppercase text-white/40"
      style={{ fontFamily: '"JetBrains Mono", monospace' }}
    >
      <span>
        Responses <span className="text-white/80">{responses}</span>
      </span>
      <span>
        Blocked <span className={blocked > 0 ? 'text-red-300' : 'text-white/80'}>{blocked}</span>
      </span>
      {toolHint && (
        <span className="text-cyan-300/70 animate-pulse">↳ {toolHint}</span>
      )}
    </div>
  );
}

// ─── Fonts + keyframes (injected once) ───────────────────────────────────────

function StyleShim() {
  return (
    <>
      <link
        rel="preconnect"
        href="https://fonts.googleapis.com"
      />
      <link
        rel="preconnect"
        href="https://fonts.gstatic.com"
        crossOrigin="anonymous"
      />
      <link
        href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=JetBrains+Mono:wght@400;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        @keyframes oracle-drift {
          0%   { transform: translate(0px, 0px) rotate(0deg); }
          50%  { transform: translate(-30px, 20px) rotate(2deg); }
          100% { transform: translate(0px, 0px) rotate(0deg); }
        }
        .animate-oracle-drift { animation: oracle-drift 28s ease-in-out infinite; }

        @keyframes oracle-whisper {
          0%   { opacity: 0; transform: translate(-50%, -8px); letter-spacing: 0.02em; }
          100% { opacity: 1; transform: translate(-50%, 0px); letter-spacing: 0em; }
        }
        .animate-oracle-whisper { animation: oracle-whisper 900ms ease-out both; }

        @keyframes oracle-reveal {
          0%   { opacity: 0; transform: translateY(14px); filter: blur(6px); }
          100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }
        .animate-oracle-reveal { animation: oracle-reveal 1200ms cubic-bezier(.2,.8,.2,1) both; }

        @keyframes oracle-pulse {
          0%, 100% { opacity: 0.45; }
          50%      { opacity: 1; }
        }
        .animate-oracle-pulse { animation: oracle-pulse 2.4s ease-in-out infinite; }

        @keyframes oracle-block-in {
          0%   { opacity: 0; transform: scale(1.04); }
          8%   { opacity: 1; transform: scale(1); }
          100% { opacity: 1; transform: scale(1); }
        }
        .animate-oracle-block-in { animation: oracle-block-in 320ms steps(4, end) both; }

        /* Hide scrollbars entirely on the oracle page */
        html, body { overflow: hidden; background: #000; }
      `}</style>
    </>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

/** Presenter override: reason shown when Shift+B forces the BLOCKED state. */
const MANUAL_BLOCK_REASON =
  'Your request was rejected by the safety system. safety_violations=[manual_override]';

export function OraclePage() {
  const o = useOracle();
  const [manualBlock, setManualBlock] = useState(false);

  // Shift+B: manually force the BLOCKED state (stage contingency if the
  // real Content Safety guardrail doesn't fire on cue). Shift+B again to clear.
  // See specs/003-nyu-oracle/spec.md FR-7.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.shiftKey && (e.key === 'B' || e.key === 'b')) {
        e.preventDefault();
        setManualBlock((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const showIdle = !o.callActive && !o.scene && !manualBlock;
  const showBlocked = manualBlock || (o.scene?.blocked ?? false);
  const blockReason = manualBlock ? MANUAL_BLOCK_REASON : o.scene?.blockReason;

  return (
    <div className="fixed inset-0 bg-black text-white">
      <StyleShim />

      {/* Base ambient field (always visible behind everything) */}
      <AmbientField />

      {/* Previous scene (fading out) */}
      {o.previousScene && (
        <SceneLayer
          src={o.previousScene.imageUrl}
          isCurrent={false}
          blocked={false}
        />
      )}

      {/* Current scene (fading in) */}
      {o.scene && !showBlocked && (
        <SceneLayer
          src={o.scene.imageUrl}
          isCurrent={true}
          blocked={false}
        />
      )}

      {/* BLOCKED state replaces everything visually */}
      {showBlocked && <BlockedLayer reason={blockReason} />}

      {/* Idle state */}
      {showIdle && <IdlePanel />}

      {/* User utterance floats up top while agent thinks */}
      {!showIdle && o.userUtterance && !showBlocked && (
        <UserWhisper text={o.userUtterance} />
      )}

      {/* Agent reply typography at bottom */}
      {o.scene && !showBlocked && (
        <AgentReply text={o.scene.agentText} loading={o.scene.loading} />
      )}

      {/* Tiny stat strip for the presenter */}
      <StatStrip
        responses={o.responseCount}
        blocked={o.blockedCount}
        toolHint={o.toolHint}
      />

      {/* Top-right status indicator */}
      <div
        className="absolute top-5 right-6 flex items-center gap-2 text-[10px] tracking-[0.4em] uppercase text-white/50"
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
      >
        <span
          className={`h-2 w-2 rounded-full ${
            o.callActive ? 'bg-emerald-400 animate-pulse' : 'bg-white/30'
          }`}
        />
        {o.callActive ? 'live call' : 'awaiting call'}
      </div>
    </div>
  );
}

export default OraclePage;
