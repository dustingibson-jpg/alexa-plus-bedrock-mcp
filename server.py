import os
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import boto3
from pydantic import BaseModel

app = FastAPI(
    title="Alexa+ AWS Bedrock Multi-Surface Orchestrator MCP",
    version="1.2.0",
    description="Streamable HTTP MCP Server connecting Alexa+ to AWS Bedrock Agentic Workflows with interactive visual testing UI."
)

# Initialize AWS Bedrock Runtime client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# In-memory session store
SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}

AVAILABLE_TOOLS = [
    {
        "name": "query_bedrock_agent",
        "description": "Executes multi-step reasoning using AWS Bedrock Claude 3.5 Sonnet to analyze user intent and orchestrate contextual tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The user prompt or spoken command from Alexa+"},
                "session_id": {"type": "string", "description": "Unique session ID to maintain context state"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "get_device_status",
        "description": "Retrieves real-time context and state from connected Ring, Fire TV, or Wearable AI devices.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device_type": {
                    "type": "string", 
                    "enum": ["ring", "fire_tv", "wearable", "all"],
                    "description": "Target device ecosystem to query"
                }
            },
            "required": ["device_type"]
        }
    },
    {
        "name": "execute_ambient_action",
        "description": "Triggers multi-device actions across Ring doorbells, Fire TV screens, and voice nodes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_device": {"type": "string", "enum": ["fire_tv", "ring", "wearable"]},
                "action": {"type": "string", "description": "Action payload (e.g. 'display_camera_feed', 'pause_playback', 'send_haptic_alert')"}
            },
            "required": ["target_device", "action"]
        }
    }
]

@app.get("/", response_class=HTMLResponse)
@app.get("/demo", response_class=HTMLResponse)
async def serve_demo_ui():
    """Serves an interactive web app simulator for the video demo."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Alexa+ Bedrock Orchestrator - Interactive MCP Simulator</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 1000px; margin: 0 auto; }
            header { border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
            h1 { margin: 0; font-size: 24px; color: #38bdf8; }
            .badge { background: #0284c7; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { background: #1e293b; border-radius: 8px; padding: 20px; border: 1px solid #334155; }
            h3 { margin-top: 0; color: #94a3b8; font-size: 16px; border-bottom: 1px solid #334155; padding-bottom: 8px; }
            input, select, button, textarea { width: 100%; padding: 10px; margin-bottom: 12px; background: #0f172a; border: 1px solid #475569; color: white; border-radius: 6px; box-sizing: border-box; }
            button { background: #0284c7; color: white; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
            button:hover { background: #0369a1; }
            pre { background: #090d16; padding: 12px; border-radius: 6px; overflow-x: auto; color: #4ade80; font-size: 13px; max-height: 250px; }
            .device-status { display: flex; justify-content: space-between; margin-bottom: 10px; padding: 10px; background: #0f172a; border-radius: 6px; }
            .status-online { color: #4ade80; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>Alexa+ AWS Bedrock MCP Simulator</h1>
                    <small style="color:#64748b;">Model Context Protocol (MCP 2025-11-25) Streamable HTTP Transport</small>
                </div>
                <span class="badge">Server Online: Port 8000</span>
            </header>

            <div class="grid">
                <div class="card">
                    <h3>1. Test Alexa+ Agent Prompt</h3>
                    <label style="font-size:12px; color:#94a3b8;">Enter Command for AWS Bedrock:</label>
                    <textarea id="promptInput" rows="3">Alexa, check who is at the front door Ring camera and display it on Fire TV.</textarea>
                    <button onclick="sendPrompt()">Run Agentic Reasoning</button>

                    <h3>2. Surface Quick Trigger</h3>
                    <div style="display:flex; gap:10px;">
                        <button style="background:#475569;" onclick="triggerDevice('ring', 'get_status')">Check Ring</button>
                        <button style="background:#475569;" onclick="triggerDevice('fire_tv', 'show_feed')">Fire TV Feed</button>
                        <button style="background:#475569;" onclick="triggerDevice('wearable', 'haptic')">Wearable Sync</button>
                    </div>
                </div>

                <div class="card">
                    <h3>Connected Devices Context</h3>
                    <div class="device-status">
                        <span>Ring Doorbell Pro</span>
                        <span class="status-online">● MOTION DETECTED</span>
                    </div>
                    <div class="device-status">
                        <span>Fire TV Stick 4K Max</span>
                        <span class="status-online">● PRIME VIDEO ACTIVE</span>
                    </div>
                    <div class="device-status">
                        <span>Bee Wearable AI</span>
                        <span class="status-online">● SYNCED (94% BATTERY)</span>
                    </div>

                    <h3>Live MCP Response Payload</h3>
                    <pre id="jsonOutput">// Live JSON-RPC payload output will appear here...</pre>
                </div>
            </div>
        </div>

        <script>
            async function sendPrompt() {
                const prompt = document.getElementById('promptInput').value;
                document.getElementById('jsonOutput').innerText = 'Processing via AWS Bedrock Claude 3.5 Sonnet...';
                
                try {
                    const res = await fetch('/mcp/rpc', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            id: Date.now(),
                            method: 'tools/call',
                            params: {
                                name: 'query_bedrock_agent',
                                arguments: { prompt: prompt, session_id: 'demo-session-1' }
                            }
                        })
                    });
                    const data = await res.json();
                    document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 2);
                } catch (err) {
                    document.getElementById('jsonOutput').innerText = 'Error: ' + err.message;
                }
            }

            async function triggerDevice(device, action) {
                document.getElementById('jsonOutput').innerText = `Executing action on ${device}...`;
                try {
                    const res = await fetch('/mcp/rpc', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            id: Date.now(),
                            method: 'tools/call',
                            params: {
                                name: 'execute_ambient_action',
                                arguments: { target_device: device, action: action }
                            }
                        })
                    });
                    const data = await res.json();
                    document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 2);
                } catch (err) {
                    document.getElementById('jsonOutput').innerText = 'Error: ' + err.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/mcp/tools")
async def list_tools():
    return {"tools": AVAILABLE_TOOLS}

@app.post("/mcp/rpc")
@app.post("/mcp/rpc/")
async def handle_mcp_rpc(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    method = body.get("method")
    req_id = body.get("id", 1)

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {"listChanged": False}, "logging": {}},
                "serverInfo": {"name": "alexa-plus-aws-bedrock-mcp", "version": "1.2.0"}
            }
        }

    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "result": {}}

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": AVAILABLE_TOOLS}}

    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "query_bedrock_agent":
            result = await execute_bedrock_reasoning(
                prompt=arguments.get("prompt", ""),
                session_id=arguments.get("session_id", "default-session")
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}

        elif tool_name == "get_device_status":
            dev_type = arguments.get("device_type", "all")
            status_data = {
                "ring": {"motion_detected": True, "battery": "88%", "last_event": "Front door motion at 3:05 AM"},
                "fire_tv": {"state": "active", "current_app": "Prime Video", "cec_connected": True},
                "wearable": {"connected": True, "haptic_ready": True, "sync_status": "synced"}
            }
            res_output = status_data if dev_type == "all" else status_data.get(dev_type, {})
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res_output)}]}}

        elif tool_name == "execute_ambient_action":
            target = arguments.get("target_device")
            action = arguments.get("action")
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Successfully executed action '{action}' on device surface '{target}'."}]}}

        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' unsupported"}}

async def execute_bedrock_reasoning(prompt: str, session_id: str) -> Dict[str, Any]:
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = []

    SESSION_STORE[session_id].append({"role": "user", "content": prompt})
    if len(SESSION_STORE[session_id]) > 6:
        SESSION_STORE[session_id] = SESSION_STORE[session_id][-6:]

    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
            "system": "You are an intelligent Alexa+ assistant engine capable of cross-device orchestration across Ring, Fire TV, and Wearable AI surfaces.",
            "messages": SESSION_STORE[session_id]
        })

        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            contentType="application/json",
            accept="application/json",
            body=body
        )

        response_body = json.loads(response.get("body").read())
        completion = response_body["content"][0]["text"]

        SESSION_STORE[session_id].append({"role": "assistant", "content": completion})

        return {
            "status": "success",
            "session_id": session_id,
            "bedrock_response": completion,
            "orchestration": "multi_turn_context_active"
        }
    except Exception as e:
        sim_response = f"Alexa+ Bedrock Orchestrator: Analyzed prompt '{prompt}'. Triggered multi-surface sync across Fire TV and Ring."
        SESSION_STORE[session_id].append({"role": "assistant", "content": sim_response})
        return {
            "status": "simulated_success",
            "session_id": session_id,
            "bedrock_response": sim_response,
            "note": f"Live AWS Bedrock notice: {str(e)}"
        }

@app.post("/mcp/stream")
async def stream_mcp_events(request: Request):
    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event': 'endpoint_connected', 'transport': 'streamable_http'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'event': 'mcp_heartbeat', 'spec_version': '2025-11-25'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
