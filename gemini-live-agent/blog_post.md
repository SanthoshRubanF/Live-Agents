# How I built Aria: a real-time voice + vision AI agent with Google ADK and Gemini Live API

*By [Your Name]*

I created this content for the purposes of entering the Gemini Live Agent Challenge. #GeminiLiveAgentChallenge

---

Building a conversational AI used to mean stitching together brittle text-to-speech, disjointed LLM inference chains, and sluggish transcription APIs. The result? High latency, no situational context, and a complete inability to handle a simple human interruption. 

For my submission to the Gemini Live Agent Challenge, I wanted to build something fundamentally different. I built **Aria**, an AI assistant that sees through your camera, listens to your voice, and handles interruptions naturally — all in real-time.

Here is the technical architectural breakdown of how I made it happen.

## Why I chose Google ADK over raw WebSockets
When working with the shiny new Gemini Live API (`gemini-3.1-pro-preview`), it’s tempting to immediately write raw WebSockets and manually construct the complex JSON-serialized Protobuf arrays the Generative AI Python SDK expects. 

I quickly realized that doing so meant reinventing the wheel. 

Instead, I used the **Google Agent Development Kit (ADK)**. ADK provides a robust, high-level structural framework for defining Agents, mounting Tools (like Google Search for factual grounding), and managing persistent multi-turn sessions. By letting ADK handle the intense routing orchestration, I was free to focus entirely on the core connection logic rather than manually juggling JSON schema validations and payload chunking.

## The Magic of LiveRequestQueue
The secret to true bidirectional audio streaming lies inside ADK's `LiveRequestQueue` architecture. 

When establishing a `StreamingMode.BIDI` session, the ADK completely abstracts the asynchronous flow. I simply pump raw `genai_types.Blob` buffers of PCM audio into an asynchronous `input_queue`, and the ADK internally streams those frames up to Vertex AI. Meanwhile, the `Runner.stream()` generator relentlessly yields back parsed output chunks (transcripts, status updates, and audio frames) that I can immediately forward down to my frontend clients. It essentially gives you a full-duplex pipe directly into the LLM's sensory cortex.

## Reversing the Pipeline: 16kHz to 24kHz
Working with raw PCM Integer-16 audio across browser boundaries is notoriously difficult. 

1. **Microphone Capture:** Using the `Web Audio API` and a `ScriptProcessorNode`, my vanilla JavaScript frontend captures floating-point audio, calculates the RMS for Voice Activity Detection (VAD), downsamples it to a hard 16kHz, and converts it to Int16 payloads.
2. **The Cloud Trip:** These raw bytes are fired up a WebSocket to my FastAPI backend and straight into the Gemini Live API.
3. **The Return Trip:** Gemini synthesizes its voice responses on the fly and returns **24kHz** PCM audio. 
4. **Resampling and Playback:** When the frontend receives this binary response, it converts the Int16 bytes back to `Float32`, creates an `AudioBuffer` explicitly rated at 24kHz, and uses a custom queue scheduler to ensure gapless, uninterrupted playback.

## Implementing True Barge-In Interruption
What happens if Aria is speaking, but the user suddenly changes their mind?

Because I run VAD locally on the client, the moment my RMS algorithm thresholds upward—even while Aria is mid-sentence—the client fires a strict `{type: "interrupt"}` JSON payload. My Python backend intercepts this, calls `runner.cancel_turn(session_id)` against the ADK, and instantly updates the status. Aria stops generating tokens immediately, drops her active context queue, and begins processing the user's new audio stream seamlessly. No glitching, no weird latency buffers. 

## Cloud Run Deployment Tips for Long-Lived WebSockets
Deploying this pipeline to Google Cloud Run required tuning a few critical settings:
- **Timeouts:** Cloud Run limits requests by default to 5 minutes. WebSocket streaming often exceeds this; defining `--timeout=3600` in your `gcloud run deploy` command is essential.
- **Workers:** WebSockets hold persistent HTTP threads. I configured my container to strictly run exactly 1 Uvicorn worker per instance (`--workers 1`) but relied on Cloud Run's native autoscaling (`--max-instances 10`) to explicitly scale out horizontally as new user sessions arrived.
- **Vertex AI:** While local API keys work for rapid prototyping, switching `GOOGLE_GENAI_USE_VERTEXAI=TRUE` ensures I’m utilizing my secured Google Cloud project structure and IAM bindings when fully deployed in production.

## What Surprised Me
The sheer speed. When utilizing the optimal PCM pipelines without overhead, the Gemini Live API consistently returned synthesized conversational tokens with *sub-500ms* real-world latency. It finally feels like speaking to a person, not a prompt box.

---

I created this content for the purposes of entering the Gemini Live Agent Challenge. #GeminiLiveAgentChallenge
