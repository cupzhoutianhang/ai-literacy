"""Lesson 06: a minimal, local MCP-shaped server.

The protocol dispatcher is deliberately implemented with only the standard
library.  If the optional ``mcp`` package is installed, this file still makes
an excellent teaching fixture: students can map each method to the official
SDK's resource/tool decorators without needing a remote service.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "sensors.csv"
PROCEDURE = ROOT / "data" / "pressure-procedure.md"


def _rows() -> list[dict[str, Any]]:
    with DATA.open(encoding="utf-8", newline="") as f:
        return [{**r, "value": float(r["value"])} for r in csv.DictReader(f)]


class LocalMCPServer:
    """JSON-RPC-like MCP subset: initialize, resources, tools and tool calls."""

    def __init__(self) -> None:
        self.rows = _rows()

    def _query(self, equipment: str, sensor: str) -> dict[str, Any]:
        found = [r for r in self.rows if r["equipment"] == equipment and r["sensor"] == sensor]
        if not found:
            raise ValueError(f"No reading for {equipment}/{sensor}")
        return sorted(found, key=lambda r: r["timestamp"])[-1]

    def dispatch(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        if method == "initialize":
            return {"protocolVersion": "2025-03-26", "serverInfo": {"name": "energy-mcp-demo", "version": "0.1"}, "capabilities": {"resources": {}, "tools": {}}}
        if method == "resources/list":
            return {"resources": [{"uri": "energy://sensors", "name": "Sensor readings", "mimeType": "text/csv"}, {"uri": "energy://procedures/pressure-drop", "name": "Pressure-drop procedure", "mimeType": "text/markdown"}]}
        if method == "resources/read":
            uri = params.get("uri")
            if uri == "energy://sensors":
                text = "timestamp,equipment,sensor,value,unit\n" + "\n".join(",".join(str(r[k]) for k in ("timestamp", "equipment", "sensor", "value", "unit")) for r in self.rows)
                return {"contents": [{"uri": uri, "mimeType": "text/csv", "text": text}]}
            if uri == "energy://procedures/pressure-drop":
                return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": PROCEDURE.read_text(encoding="utf-8")}]}
            raise ValueError(f"Unknown resource: {uri}")
        if method == "tools/list":
            return {"tools": [{"name": "query_sensor", "description": "Read the latest sensor value", "inputSchema": {"type": "object", "properties": {"equipment": {"type": "string"}, "sensor": {"type": "string"}}, "required": ["equipment", "sensor"]}}, {"name": "calculate_pressure_drop", "description": "Compute inlet minus outlet pressure", "inputSchema": {"type": "object", "properties": {"equipment": {"type": "string"}}, "required": ["equipment"]}}]}
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            if name == "query_sensor":
                result = self._query(args["equipment"], args["sensor"])
            elif name == "calculate_pressure_drop":
                inlet = self._query(args["equipment"], "pressure_in")
                outlet = self._query(args["equipment"], "pressure_out")
                result = {"equipment": args["equipment"], "drop": round(inlet["value"] - outlet["value"], 3), "unit": inlet["unit"], "timestamp": max(inlet["timestamp"], outlet["timestamp"])}
            else:
                raise ValueError(f"Unknown tool: {name}")
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "structuredContent": result}
        raise ValueError(f"Unsupported method: {method}")


class LocalMCPClient:
    def __init__(self, server: LocalMCPServer | None = None) -> None:
        self.server = server or LocalMCPServer()

    def request(self, method: str, **params: Any) -> dict[str, Any]:
        return self.server.dispatch(method, params)


def run_stdio() -> None:
    """Read one JSON request per line and emit one JSON response per line."""
    server = LocalMCPServer()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            result = server.dispatch(request["method"], request.get("params", {}))
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        except Exception as exc:  # protocol errors are returned, not swallowed
            response = {"jsonrpc": "2.0", "id": request.get("id") if "request" in locals() else None, "error": {"code": -32602, "message": str(exc)}}
        print(json.dumps(response, ensure_ascii=False), flush=True)


def demo() -> dict[str, Any]:
    client = LocalMCPClient()
    return {"initialize": client.request("initialize"), "resources": client.request("resources/list"), "tools": client.request("tools/list"), "call": client.request("tools/call", name="calculate_pressure_drop", arguments={"equipment": "pump-A"})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdio", action="store_true", help="Run the newline-delimited protocol server")
    args = parser.parse_args()
    print(json.dumps(demo() if not args.stdio else {}, ensure_ascii=False, indent=2)) if not args.stdio else run_stdio()


if __name__ == "__main__":
    main()
