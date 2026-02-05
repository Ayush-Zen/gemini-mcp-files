#!/usr/bin/env python3
"""
Gemini MCP JSON-RPC 2.0 compliant Kali Linux Tools Server
NO FastMCP – manual, explicit MCP implementation
"""

import argparse
import subprocess
import logging
from flask import Flask, request, jsonify

# ---------------- CONFIG ----------------
PORT = 5000
TIMEOUT = 300

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("kali-mcp")

# ---------------- APP ----------------
app = Flask(__name__)

# ---------------- COMMAND EXEC ----------------
def run(cmd: str) -> str:
    log.info(f"[EXEC] {cmd}")
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        return proc.stdout or proc.stderr
    except Exception as e:
        return str(e)

# ======================================================
# MCP JSON-RPC ENDPOINT (Gemini talks ONLY to /)
# ======================================================
@app.route("/", methods=["POST"])
def mcp_rpc():
    req = request.get_json(force=True, silent=True) or {}

    jsonrpc = req.get("jsonrpc")
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    if jsonrpc != "2.0":
        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32600, "message": "Invalid JSON-RPC version"}
        })

    # ================= INITIALIZE =================
    if method == "initialize":
        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "kali-mcp",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        })

    # ================= TOOLS LIST =================
    if method == "tools/list":
        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": "nmap_scan", "description": "Run Nmap scan", "inputSchema": {"type": "object","properties":{"target":{"type":"string"}},"required":["target"]}},
                    {"name": "gobuster_scan", "description": "Run Gobuster directory scan", "inputSchema": {"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}},
                    {"name": "dirb_scan", "description": "Run Dirb scan", "inputSchema": {"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}},
                    {"name": "nikto_scan", "description": "Run Nikto scan", "inputSchema": {"type":"object","properties":{"target":{"type":"string"}},"required":["target"]}},
                    {"name": "sqlmap_scan", "description": "Run SQLMap scan", "inputSchema": {"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}},
                    {"name": "wpscan_analyze", "description": "Run WPScan", "inputSchema": {"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}},
                    {"name": "enum4linux_scan", "description": "Run Enum4linux", "inputSchema": {"type":"object","properties":{"target":{"type":"string"}},"required":["target"]}},
                    {"name": "hydra_attack", "description": "Run Hydra brute force", "inputSchema": {"type":"object","properties":{"target":{"type":"string"},"service":{"type":"string"}},"required":["target","service"]}},
                    {"name": "john_crack", "description": "Run John the Ripper", "inputSchema": {"type":"object","properties":{"hash_file":{"type":"string"}},"required":["hash_file"]}},
                    {"name": "metasploit_run", "description": "Run Metasploit module", "inputSchema": {"type":"object","properties":{"module":{"type":"string"}},"required":["module"]}},
                    {"name": "execute_command", "description": "Execute arbitrary command", "inputSchema": {"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}
                ]
            }
        })

    # ================= TOOLS CALL =================
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "nmap_scan":
            output = run(f"nmap -sCV {args['target']}")
        elif name == "gobuster_scan":
            output = run(f"gobuster dir -u {args['url']} -w /usr/share/wordlists/dirb/common.txt")
        elif name == "dirb_scan":
            output = run(f"dirb {args['url']}")
        elif name == "nikto_scan":
            output = run(f"nikto -h {args['target']}")
        elif name == "sqlmap_scan":
            output = run(f"sqlmap -u {args['url']} --batch")
        elif name == "wpscan_analyze":
            output = run(f"wpscan --url {args['url']}")
        elif name == "enum4linux_scan":
            output = run(f"enum4linux -a {args['target']}")
        elif name == "hydra_attack":
            output = run(f"hydra {args['target']} {args['service']}")
        elif name == "john_crack":
            output = run(f"john {args['hash_file']}")
        elif name == "metasploit_run":
            output = run(f"msfconsole -q -x 'use {args['module']}; run; exit'")
        elif name == "execute_command":
            output = run(args["command"])
        else:
            output = f"Unknown tool: {name}"

        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": output}
                ]
            }
        })

    # ================= UNKNOWN METHOD =================
    return jsonify({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": "Method not found"}
    })

# ---------------- MAIN ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    log.info(f"Starting Gemini MCP Kali server on {args.ip}:{args.port}")
    app.run(host=args.ip, port=args.port)
