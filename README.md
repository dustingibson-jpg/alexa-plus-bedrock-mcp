# Alexa+ AWS Bedrock Orchestrator MCP

[![Python Test Suite](https://github.com/dustingibson-jpg/alexa-plus-bedrock-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/dustingibson-jpg/alexa-plus-bedrock-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Spec](https://img.shields.io/badge/MCP%20Spec-2025--11--25-blue.svg)](https://modelcontextprotocol.io)

An enterprise-grade, open-source Streamable HTTP Model Context Protocol (MCP 2025-11-25) server integrating **Alexa+** voice intents with **AWS Bedrock** (`anthropic.claude-3-5-sonnet`) for multi-surface device orchestration across Ring, Fire TV, and Wearable AI.

---

## Key Features

- **Full MCP Protocol Compliance**: Implements MCP 2025-11-25 JSON-RPC transport via FastAPI (`initialize`, `tools/list`, `tools/call`, `prompts/list`, `prompts/get`, `resources/list`, `resources/read`).
- **AWS Bedrock Orchestration**: Uses `boto3` to stream user prompts through Anthropic Claude 3.5 Sonnet on AWS Bedrock for intent evaluation and multi-step reasoning.
- **Multi-Surface Coordination**: Triggers contextual ambient actions across Ring doorbells, Fire TV video streams, and Wearable AI haptic sync.
- **Embedded Web Simulator**: Serves an interactive simulator UI at `http://localhost:8000` to visualize JSON-RPC request and response payloads in real time.
- **CORS & Inspection Ready**: Configured with CORS middleware for compatibility with external MCP inspector tools.
- **Automated CI/CD**: Verified with `pytest` unit testing and GitHub Actions workflow on every push.

---

## MCP Capabilities Schema

### Tools
1. `query_bedrock_agent`: Evaluates intent and executes agentic reasoning on AWS Bedrock.
2. `get_device_status`: Fetches telemetry from Ring, Fire TV, or Wearables.
3. `execute_ambient_action`: Executes multi-device actions (e.g., displaying camera feed on Fire TV).

### Prompts
1. `smart_home_routine_assistant`: Template for multi-device ambient automation.
2. `security_sweep_audit`: System prompt for automated Ring/Fire TV security checks.

### Resources
1. `ambient://device_logs`: Real-time telemetry event stream.
2. `ambient://session_summary`: Multi-turn conversational session context.

---

## Quickstart

### Prerequisites
- Python 3.9+
- AWS Credentials configured with Bedrock access (`us-east-1` default)

### Installation & Execution

```bash
# Clone repository
git clone [https://github.com/dustingibson-jpg/alexa-plus-bedrock-mcp.git](https://github.com/dustingibson-jpg/alexa-plus-bedrock-mcp.git)
cd alexa-plus-bedrock-mcp

# Install dependencies
pip install -r requirements.txt

# Run unit test suite
python3 -m pytest test_server.py

# Launch MCP Server & Web Simulator
python3 server.py
