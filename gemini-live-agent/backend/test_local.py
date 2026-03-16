"""
Local Test Script for Gemini Live Agent backend.

End-to-end tests without a browser over HTTP and WebSockets.
"""

import asyncio
import json
import math
import struct
import base64
import time
from urllib.parse import urljoin

import httpx
import websockets
from PIL import Image
import io

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

def print_result(name: str, passed: bool, duration: float, error: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"{status} - {name} ({duration:.2f}s)"
    if error:
        msg += f" - {error}"
    print(msg)

async def test_health():
    """TEST 1: Health check"""
    print("\n--- Running TEST 1: Health check ---")
    start = time.time()
    passed = False
    error = ""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(urljoin(BASE_URL, "/health"))
            resp.raise_for_status()
            data = resp.json()
            assert data.get("status") == "ok", f"Expected status 'ok', got: {data.get('status')}"
            print(f"Health response: {json.dumps(data, indent=2)}")
            passed = True
    except Exception as e:
        error = str(e)
    
    duration = time.time() - start
    print_result("Health Check", passed, duration, error)
    return passed

async def test_text_turn():
    """TEST 2: WebSocket text turn"""
    print("\n--- Running TEST 2: WebSocket text turn ---")
    start = time.time()
    passed = False
    error = ""
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send text
            req = {"type": "text", "content": "Hello Pallavee, what is 2 + 2?"}
            print(f"Sending: {req}")
            await websocket.send(json.dumps(req))
            
            # Send end turn
            await websocket.send(json.dumps({"type": "end_turn"}))
            
            agent_transcript_received = False
            
            # Wait for responses
            while True:
                try:
                    # Timeout after 10 seconds of no messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    
                    if isinstance(message, str):
                        data = json.loads(message)
                        print(f"Received JSON: {data}")
                        if data.get("type") == "transcript" and data.get("role") == "agent":
                            agent_transcript_received = True
                            # Optional: we can break early if we just want one response,
                            # but usually we want to see the whole turn. We'll break after receiving it and thinking state changes.
                            
                        # If agent goes back to idle/listening, turn is over
                        if data.get("type") == "status" and data.get("state") == "listening" and agent_transcript_received:
                            break
                            
                    else:
                        print(f"Received binary frame of {len(message)} bytes")
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for more messages.")
                    break
            
            assert agent_transcript_received, "Did not receive transcript from agent."
            passed = True
            
    except Exception as e:
        error = str(e)
        print(f"Error during execution: {e}")
        
    duration = time.time() - start
    print_result("WebSocket Text Turn", passed, duration, error)
    return passed

def generate_sine_wave(duration_sec: float, freq: float = 440.0, sample_rate: int = 16000) -> bytes:
    """Generate a PCM Int16 sine wave."""
    samples = int(duration_sec * sample_rate)
    buffer = bytearray()
    for i in range(samples):
        # Sine wave formula: A * sin(2 * pi * f * t)
        t = i / sample_rate
        val = int(32767.0 * math.sin(2 * math.pi * freq * t))
        # pack as little-endian short
        buffer.extend(struct.pack('<h', val))
    return bytes(buffer)

async def test_audio_simulation():
    """TEST 3: WebSocket audio simulation"""
    print("\n--- Running TEST 3: WebSocket audio simulation ---")
    start = time.time()
    passed = False
    error = ""
    total_received_bytes = 0
    output_filename = "test_output.pcm"
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Generate 2 seconds of 440Hz tone
            print("Generating 2 seconds of sine wave (16kHz)...")
            audio_data = generate_sine_wave(2.0)
            
            # Send in 100ms chunks (1600 samples = 3200 bytes)
            chunk_size = 3200
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                await websocket.send(chunk)
                await asyncio.sleep(0.1) # Simulate real-time streaming
                
            # Tell agent we stopped speaking
            print("Finished sending audio. Sending end_turn...")
            await websocket.send(json.dumps({"type": "end_turn"}))
            
            binary_received = False
            
            with open(output_filename, "wb") as f_out:
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        if isinstance(message, bytes):
                            binary_received = True
                            f_out.write(message)
                            total_received_bytes += len(message)
                        elif isinstance(message, str):
                            data = json.loads(message)
                            # print(f"JSON: {data}")
                            if data.get("type") == "status" and data.get("state") == "listening" and binary_received:
                                print("Agent finished speaking.")
                                break
                    except asyncio.TimeoutError:
                        break
                        
            print(f"Received {total_received_bytes} bytes of audio response.")
            assert binary_received and total_received_bytes > 0, "No binary audio received back."
            passed = True
            
    except Exception as e:
        error = str(e)
        print(f"Error during execution: {e}")
        
    duration = time.time() - start
    print_result("WebSocket Audio Simulation", passed, duration, error)
    return passed

def create_test_image_b64() -> str:
    """Create a 320x240 red solid JPEG in memory and return as base64."""
    img = Image.new('RGB', (320, 240), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=80)
    img_bytes = buf.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

async def test_image_injection():
    """TEST 4: Image injection"""
    print("\n--- Running TEST 4: Image injection ---")
    start = time.time()
    passed = False
    error = ""
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("Creating solid red test image...")
            b64_img = create_test_image_b64()
            
            print("Sending image...")
            await websocket.send(json.dumps({
                "type": "image",
                "data": b64_img
            }))
            
            prompt = "What color is the image you see?"
            print(f"Sending prompt: {prompt}")
            await websocket.send(json.dumps({
                "type": "text",
                "content": prompt
            }))
            await websocket.send(json.dumps({"type": "end_turn"}))
            
            agent_responded = False
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    if isinstance(message, str):
                        data = json.loads(message)
                        if data.get("type") == "transcript" and data.get("role") == "agent":
                            print(f"Agent response: {data.get('text')}")
                            agent_responded = True
                        if data.get("type") == "status" and data.get("state") == "listening" and agent_responded:
                            break
                except asyncio.TimeoutError:
                    print("Timeout waiting for image vision response.")
                    break
                    
            assert agent_responded, "Did not get a vision response from the agent."
            passed = True
            
    except Exception as e:
        error = str(e)
        print(f"Error during execution: {e}")
        
    duration = time.time() - start
    print_result("Image Injection", passed, duration, error)
    return passed


async def main():
    print("==================================================")
    print("  GEMINI LIVE AGENT - LOCAL INTEGRATION TESTS")
    print("==================================================")
    print("\nMake sure the server is running natively before running these tests.")
    print("Command to start server:")
    print("  cd backend && uvicorn main:app --reload --port 8000")
    print("\nStarting tests...\n")
    
    results = []
    
    # Run tests sequentially
    results.append(await test_health())
    # Sleep briefly to let server GC connections
    await asyncio.sleep(1)
    
    results.append(await test_text_turn())
    await asyncio.sleep(1)
    
    results.append(await test_audio_simulation())
    await asyncio.sleep(1)
    
    results.append(await test_image_injection())
    
    print("\n==================================================")
    print(f"  TESTS COMPLETE: {sum(results)}/{len(results)} PASSED")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
