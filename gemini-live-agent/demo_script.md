# Pallavee — Gemini Live Agent
### 4-Minute Devpost Demo Script

---
**[0:00–0:25] THE HOOK**

**SCREEN ACTION:**
Open a traditional chatbot interface (like standard ChatGPT/Gemini). Type a question: "What is the capital of France?". Wait a few seconds. A large block of text appears. The user sighs, types another question, waits again.

**NARRATION (High Energy & Direct):**
"This is how we've been interacting with AI since the beginning. You type. You wait. You read. And you repeat. It's powerful, but it's not a conversation. It's a terminal. What if AI didn't wait for your keystrokes? What if it could just... *talk back*? Right here, right now?"

---
**[0:25–0:50] INTRODUCTION & SETUP**

**SCREEN ACTION:**
Cut to a fresh browser tab opening the "Pallavee" Live Agent UI. 
The mouse clicks **[▶ Start]**. 
The status indicator in the top right flashes "Connecting" and then snaps to a bright green **"● Live"**. 
The user speaks directly into the microphone without clicking anything else.

**NARRATION:**
"Meet Pallavee. Built for the Gemini Live Agent Challenge. She isn’t waiting for a text payload. She’s listening right now. Always on. Always ready."

---
**[0:50–1:40] VOICE DEMO & BARGE-IN**

**SCREEN ACTION:**
- **User speaks:** "Hey Pallavee, what's the current weather like in Chennai?"
- **UI:** The agent state immediately switches to `Thinking...` and less than a second later, the waveform visualizer starts bouncing rhythmically. 
- **Pallavee speaks (synthesized audio):** "Right now, Chennai is experiencing partly cloudy skies with temperatures around 32 degrees Celsius, and high humidity..."
- **User INTERRUPTS (mid-sentence):** "Wait — what about Mumbai?"
- **UI:** The waveform *instantly* drops flat. The state snaps back to `Listening`.
- **Pallavee speaks (instantly pivoting):** "Oh, sure! In Mumbai, it's currently sunny and about 30 degrees..."

**NARRATION:**
"With Pallavee, there’s zero latency friction. Notice how fast she responds? Less than half a second. And the best part? She doesn't need you to politely wait your turn. If she's talking, just interrupt her. Thanks to robust Web Audio API handling, she drops what she's doing and pivots instantly, exactly like a real human conversation."

---
**[1:40–2:30] VISION & GROUNDING**

**SCREEN ACTION:**
- **User clicks:** **[📷 Camera On]**. The 240x180 live feed appears on the left.
- **User holds up an object:** (e.g., a physical book, a specific laptop, or a coffee cup).
- **User speaks:** "Pallavee, what is this? Tell me something interesting about it."
- **Pallavee speaks:** "I see you're holding a MacBook Pro with the M3 chip. Those were announced in late 2023..."
- **User follows up:** "Oh wow. Should I buy a newer version right now?"
- **UI:** Briefly shows the `Thinking` state as the backend hits the Google Search tool.
- **Pallavee speaks:** "According to a search I just ran, Apple recently announced the new M4 MacBook Pros last week. If you value the latest performance jump, you might want to consider the newer model."

**NARRATION:**
"But Pallavee isn't just a voice. She's got eyes. By streaming low-latency camera frames straight to the Gemini Live API, she literally sees what you see. And when you ask her for advice? She never hallucinates. Using Google ADK tool mounting, she actively searches the live web for up-to-date facts before saying a single word."

---
**[2:30–3:15] ARCHITECTURE**

**SCREEN ACTION:**
Cut to the `architecture_diagram.png`.
Highlight the *Browser* box. Then draw a line to *Cloud Run*. Then to *Vertex AI*. 
Zoom in on the `Bidi stream (audio + vision)` arrow.

**NARRATION:**
"So, how does it work under the hood? It’s a beautifully orchestrated pipeline. The browser captures raw 16kHz PCM audio and Base64 vision frames, firing them through a persistent WebSocket. Our Python FastAPI backend manages the session using Google ADK. That backend hooks directly into Vertex AI's Gemini 2.5 Flash streaming endpoint, synthesizing audio on the fly and piping it straight back to the user."

---
**[3:15–3:45] CLOUD DEPLOYMENT PROOF**

**SCREEN ACTION:**
Cut to the Google Cloud Console. 
Show the Cloud Run Services page highlighting `gemini-live-agent`. 
Click into the Logs tab. 
Show a waterfall of live JSON streaming logs from the session that was just recorded, focusing on the `Session ID` and `Duration` metrics logging successfully.

**NARRATION:**
"And this isn't running on a local laptop constraint. It is fully containerized and deployed natively on Google Cloud Run. It’s globally scalable, features zero cold starts for the WebSocket server, and handles simultaneous user sessions completely asynchronously."

---
**[3:45–4:00] CLOSING**

**SCREEN ACTION:**
Fade to a dark, sleek title card.
Text on screen:
**Pallavee — Gemini Live Agent**
**GitHub:** github.com/your-username/gemini-live-agent
**Live:** gemini-live-agent-xyz.a.run.app 

**NARRATION:**
"Pallavee. Built exclusively for the Gemini Live Agent Challenge. Try it yourself using the repo link below. Because this is exactly what AI conversation should feel like. Thank you."
