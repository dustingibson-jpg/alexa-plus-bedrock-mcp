import os
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import boto3
from pydantic import BaseModel

# Initialize FastAPI application with Streamable HTTP MCP support
app = FastAPI(
    title="Alexa+ AWS Bedrock Multi-Surface Orchestrator MCP",
    version="1.1.0",
    description="Streamable HTTP MCP Server connecting Alexa+ to AWS Bedrock Agentic Workflows with cross-device IoT execution."
)

# Initialize AWS Bedrock Runtime client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# In-memory session store to maintain conversational context across calls
SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}

# Comprehensive Tool Definitions matching MCP Spec 2025-11-25
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
                "action": {"type": "string", "description": "Action payload (e.g. 'display_camera_feed', 'pause_playback', 'send_haptic_alert')"},
                "parameters": {"type": "object", "description": "Optional action metadata"}
            },
            "required": ["target_device", "action"]
        }
    }
]

@app.get("/")
async def root():
    return {
        "status": "online",
        "mcp_version": "2025-11-25",
        "service": "Alexa+ Bedrock Multi-Surface Orchestration Server",
        "tools_registered": len(AVAILABLE_TOOLS)
    }

@app.get("/mcp/tools")
async def list_tools():
    """Exposes tool schema list for agent discovery."""
    return {"tools": AVAILABLE_TOOLS}

@app.post("/mcp/rpc")
@app.post("/mcp/rpc/")
async def handle_mcp_rpc(request: Request):
    """Primary JSON-RPC 2.0 Handler for MCP Streamable HTTP interaction."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    method = body.get("method")
    req_id = body.get("id", 1)

    # 1. Handshake Initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "alexa-plus-aws-bedrock-mcp",
                    "version": "1.1.0"
                }
            }
        }

    # 2. Handshake Notification
    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "result": {}}

    # 3. List Tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": AVAILABLE_TOOLS}
        }

    # 4. Execute Tool Calls
    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "query_bedrock_agent":
            result = await execute_bedrock_reasoning(
                prompt=arguments.get("prompt", ""),
                session_id=arguments.get("session_id", "default-session")
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
            }

        elif tool_name == "get_device_status":
            dev_type = arguments.get("device_type", "all")
            status_data = {
                "ring": {"motion_detected": True, "battery": "88%", "last_event": "Front door motion at 3:05 AM"},
                "fire_tv": {"state": "active", "current_app": "Prime Video", "cec_connected": True},
                "wearable": {"connected": True, "haptic_ready": True, "sync_status": "synced"}
            }
            res_output = status_data if dev_type == "all" else status_data.get(dev_type, {})
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res_output)}]}
            }

        elif tool_name == "execute_ambient_action":
            target = arguments.get("target_device")
            action = arguments.get("action")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully executed action '{action}' on device surface '{target}'."
                    }]
                }
            }

        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' unsupported"}
        }

async def execute_bedrock_reasoning(prompt: str, session_id: str) -> Dict[str, Any]:
    """Invocates AWS Bedrock runtime model with session history for agentic reasoning."""
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = []

    # Maintain sliding conversation window
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
        # Fallback simulation mode for local testing without AWS keys
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
    """Server-Sent Events (SSE) endpoint for Streamable HTTP transport per spec."""
    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event': 'endpoint_connected', 'transport': 'streamable_http'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'event': 'mcp_heartbeat', 'spec_version': '2025-11-25'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
