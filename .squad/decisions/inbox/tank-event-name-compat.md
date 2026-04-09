# Decision: Handle Both Preview and GA Realtime Transcript Event Names

**Date:** 2026-04-09
**Author:** Tank (Backend Dev)
**Status:** Implemented
**Commit:** 297e7f7

## Context

The Azure OpenAI Realtime API uses different event names depending on the API version:
- **Preview** (`2025-04-01-preview`): `response.audio_transcript.done` / `.delta`
- **GA**: `response.output_audio_transcript.done` / `.delta`

Our backend is pinned to the preview API version (`config.py:189`), but a previous fix (commit 2669075) changed the handler to only listen for the GA name. This caused agent speech transcripts to be silently dropped — the event arrived but never matched the handler.

## Decision

Handle **both** event names in `media_ws.py` using `if t in (preview_name, ga_name)`. This makes the code forward-compatible: it works on the current preview API and will continue working when we upgrade to GA without any code changes.

## Implications

- When upgrading the API version to GA, no transcript handler changes needed.
- The delta ignore list already covered both names — only the `.done` handler needed fixing.
- Pattern to follow: any event name that differs between preview/GA should be handled with a tuple check, not a single string comparison.
