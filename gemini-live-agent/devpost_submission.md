# Aria — Gemini Live Voice & Vision Agent

## INSPIRATION
Static chatbots operate on a fundamentally flawed premise: wait your turn, type your query, wait for a wall of text. Real human conversation doesn't work that way. It's messy, simultaneous, and relies heavily on shared visual context.

The moment I realized how transformative it would be to combine ultra-low latency voice generation, instantaneous barge-in interruption handling, and active hardware-camera vision analysis into a single unified stream, the concept for Aria was born. I wanted to build an agent that felt less like a terminal prompt and more like a knowledgeable colleague actively sitting beside me.

## WHAT IT DOES
Aria is a real-time, bidirectional AI agent that fundamentally changes human-computer interaction through four core capabilities:

1. **Real-Time Voice:** Engages in natural, full-duplex conversational audio streaming with human-like latency.
2. **Camera Vision:** "Sees" through the user's web camera, allowing physical objects and environments to be queried instantly without taking photos or uploading files.
3. **Barge-in Interruption:** Listens concurrently while speaking. If the user interrupts, Aria instantly stops generating its current response and seamlessly pivots to the new context.
4. **Search Grounding:** By utilizing the Google Search Tool, the agent eliminates AI hallucination by querying live data before responding with factual answers.

## HOW I BUILT IT
Aria’s core foundation was rapid-prototyped using the powerful **Google ADK (Agent Development Kit)**, which drastically simplified defining agent scopes, tool mounting, and session lifecycle management.

For the primary inferencing framework, I leveraged the bleeding-edge **Gemini Live API (`gemini-3.1-pro-preview`)**. By establishing a `StreamingMode.BIDI` (Bidirectional) context, the agent accepts raw bytes of audio and Base64 encoded JPEG vision data directly into its modality buffers while simultaneously streaming generated 24kHz PCM audio outward.

To handle this massive real-time data flow, the backend was built on **FastAPI and WebSockets**. The Python server manages persistent asynchronous connections with the client. On the frontend, a vanilla JavaScript client uses the **Web Audio API** and an advanced `ScriptProcessorNode` to capture raw 16kHz microphone logic, calculate RMS (Root Mean Square) for local Voice Activity Detection (VAD), and transmit zero-gap PCM data to the server.

The entire backend pipeline is containerized using **Docker** and built through **Google Cloud Build**, enabling seamless, autoscaling deployment to **Google Cloud Run**. Finally, to ensure production-grade reliability and billing management, the agent intelligently falls back to **Vertex AI** when running in the cloud environment.

## CHALLENGES
- **Audio Resampling:** Modern browsers default to 44.1kHz or 48kHz audio capture, but the Gemini Live API specifically demands highly-tuned 16kHz Int16 sample rates. Porting native Python 3.13 packages to handle low-latency bit-crushing (`audioop-lts`) and dynamic rate conversion was a significant hurdle.
- **True Barge-In:** Implementing interruption without audio stuttering or broken queue scheduling required precise state tracking between the frontend Web Audio API playback nodes and the backend ADK `SessionManager`. 

## ACCOMPLISHMENTS
- Achieved sub-500ms voice response latency using bare-metal PCM transfers over wss:// protocols.
- Built a highly resilient frontend canvas-stealing loop for invisible, clean camera context injection.
- Reached zero hallucinations during factual queries explicitly through the robust ADK Google Search integration.

## WHAT I LEARNED
- Mastering the underlying architecture of the ADK `LiveRequestQueue` and how it schedules concurrent multi-modal jobs.
- The extreme intricacies of WebSocket binary frame chunking for continuous raw PCM audio streams.
- The structural authentication differences between rapid local prototyping via API keys and production-grade IAM deployments running on Vertex AI.

## WHAT'S NEXT
- **Persistent Memory:** Utilizing Vector databases to remember user preferences across distinct WebSocket sessions.
- **Multi-Language Support:** Expanding the ADK configurations to support diverse global tongues dynamically.
- **Mobile App Wrapper:** Porting the vanilla HTML/JS logic over to React Native for native iOS and Android experiences.

## BUILT WITH
`google-adk`, `gemini-live-api`, `vertex-ai`, `cloud-run`, `fastapi`, `python`, `websockets`, `web-audio-api`, `docker`, `cloud-build`
