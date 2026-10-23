import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_mcp_initialize():
    response = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["protocolVersion"] == "2025-11-25"

def test_mcp_list_tools():
    response = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    assert len(tools) == 3

def test_mcp_list_prompts():
    response = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "prompts/list",
        "params": {}
    })
    assert response.status_code == 200
    prompts = response.json()["result"]["prompts"]
    assert len(prompts) == 2

def test_mcp_list_resources():
    response = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 4,
        "method": "resources/list",
        "params": {}
    })
    assert response.status_code == 200
    resources = response.json()["result"]["resources"]
    assert len(resources) == 2
