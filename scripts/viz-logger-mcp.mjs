#!/usr/bin/env node
/**
 * agent-meta viz-logger MCP Server (Node.js stdio bridge)
 * ========================================================
 *
 * Workaround for opencode on Windows being unable to send data via stdin
 * to Python child processes (Node.js child_process.spawn -> Python stdin pipe
 * hangs after process start, causing a 30s timeout and EOF).
 *
 * This Node.js server implements the MCP stdio JSON-RPC protocol itself and
 * delegates tool calls to `viz-logger.py` in CLI mode via `child_process.spawn`.
 *
 * Manual start for testing:
 *   node scripts/viz-logger-mcp.mjs
 * Then send JSON-RPC messages via stdin, e.g.:
 *   Content-Length: 85\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}
 *
 * Protocol flow (opencode <-> this server):
 *   1. initialize           -> server capabilities
 *   2. notifications/initialized
 *   3. tools/list           -> available tools (log_viz_event)
 *   4. tools/call           -> server spawns Python CLI process
 *   5. Python writes event  -> .meta-viz/events.jsonl
 *   6. Server returns MCP result to opencode
 *
 * No npm dependencies required — uses only Node.js built-in modules.
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');

const MCP_SERVER_NAME = "viz-logger";
const MCP_SERVER_VERSION = "1.1.0";
const MCP_PROTOCOL_VERSION = "2024-11-05";

const TOOLS = [
    {
        "name": "log_viz_event",
        "description": "Log a visualization event to the events.jsonl file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event": {
                    "type": "string",
                    "description": "Event type: agent_start, delegate_out, agent_end",
                    "enum": ["agent_start", "delegate_out", "agent_end"],
                },
                "agent": {
                    "type": "string",
                    "description": "The current agent role",
                },
                "provider": {
                    "type": "string",
                    "description": "The AI provider",
                },
                "status": {
                    "type": "string",
                    "description": "Status for agent_end",
                    "enum": ["success", "error"],
                },
                "target": {
                    "type": "string",
                    "description": "Target agent role (for delegate_out and agent_end)",
                },
                "caller": {
                    "type": "string",
                    "description": "Calling agent role (for agent_start)",
                },
                "task_id": {
                    "type": "string",
                    "description": "Correlation UUID to track delegation",
                },
                "payload": {
                    "type": "object",
                    "description": "Optional JSON payload or error message",
                },
            },
            "required": ["event", "agent"],
        },
    }
];

// ---------------------------------------------------------------------------
// JSON-RPC stdio helpers
// ---------------------------------------------------------------------------

function sendMessage(msg) {
    const data = JSON.stringify(msg);
    const payload = Buffer.from(data, 'utf-8');
    const header = `Content-Length: ${payload.length}\r\n\r\n`;
    process.stdout.write(Buffer.from(header, 'ascii'));
    process.stdout.write(payload);
}

let receiveBuffer = Buffer.alloc(0);

function tryParseMessage() {
    const headerEnd = receiveBuffer.indexOf('\r\n\r\n');
    if (headerEnd === -1) return;

    const headerStr = receiveBuffer.slice(0, headerEnd).toString('utf-8');
    const headers = {};
    for (const line of headerStr.split('\r\n')) {
        const idx = line.indexOf(':');
        if (idx !== -1) {
            headers[line.slice(0, idx).trim().toLowerCase()] = line.slice(idx + 1).trim();
        }
    }

    const length = parseInt(headers['content-length'] || '0', 10);
    if (!length) {
        receiveBuffer = receiveBuffer.slice(headerEnd + 4);
        return;
    }

    const totalLength = headerEnd + 4 + length;
    if (receiveBuffer.length < totalLength) return;

    const body = receiveBuffer.slice(headerEnd + 4, totalLength);
    receiveBuffer = receiveBuffer.slice(totalLength);

    try {
        const msg = JSON.parse(body.toString('utf-8'));
        handleMessage(msg);
    } catch (e) {
        // Invalid JSON, log to stderr and ignore
        console.error(`[viz-logger-mcp] Invalid JSON body: ${e.message}`);
    }

    // There might be another message already in the buffer
    tryParseMessage();
}

process.stdin.on('data', (chunk) => {
    receiveBuffer = Buffer.concat([receiveBuffer, chunk]);
    tryParseMessage();
});

process.stdin.on('end', () => {
    process.exit(0);
});

process.stdin.resume();

// ---------------------------------------------------------------------------
// Message handlers
// ---------------------------------------------------------------------------

function makeResponse(requestId, result = null, error = null) {
    const msg = { jsonrpc: "2.0", id: requestId };
    if (error !== null) msg.error = error;
    else msg.result = result;
    return msg;
}

function handleInitialize(requestId, params) {
    return makeResponse(requestId, {
        protocolVersion: MCP_PROTOCOL_VERSION,
        capabilities: { tools: {}, logging: {} },
        serverInfo: { name: MCP_SERVER_NAME, version: MCP_SERVER_VERSION },
    });
}

function handleToolsList(requestId, params) {
    return makeResponse(requestId, { tools: TOOLS });
}

async function handleToolsCall(requestId, params) {
    const toolName = params?.name;
    const args = params?.arguments || {};

    if (toolName !== "log_viz_event") {
        return makeResponse(requestId, null, {
            code: -32601,
            message: `Tool '${toolName}' not found`,
        });
    }

    if (!args.event || !args.agent) {
        return makeResponse(requestId, null, {
            code: -32602,
            message: "Missing required parameters: event, agent",
        });
    }

    try {
        await callPythonCli(args);
        return makeResponse(requestId, {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ success: true, event: args }),
                },
            ],
            isError: false,
        });
    } catch (e) {
        return makeResponse(requestId, {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ success: false, error: e.message }),
                },
            ],
            isError: true,
        });
    }
}

// ---------------------------------------------------------------------------
// Python CLI bridge
// ---------------------------------------------------------------------------

function callPythonCli(args) {
    return new Promise((resolve, reject) => {
        // Candidate interpreters: prefer venv, then system PATH fallbacks
        const pythonCandidates = [
            path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe'),
            path.join(PROJECT_ROOT, '.venv', 'bin', 'python'),
            'python',
            'python3',
        ];

        const scriptPath = path.join(__dirname, 'viz-logger.py');
        const cliArgs = [
            scriptPath,
            '--event', String(args.event),
            '--agent', String(args.agent),
            '--provider', String(args.provider || 'unknown'),
        ];

        if (args.status) cliArgs.push('--status', String(args.status));
        if (args.target) cliArgs.push('--target', String(args.target));
        if (args.caller) cliArgs.push('--caller', String(args.caller));
        if (args.task_id) cliArgs.push('--task_id', String(args.task_id));
        if (args.payload) {
            const payloadStr = typeof args.payload === 'string'
                ? args.payload
                : JSON.stringify(args.payload);
            cliArgs.push('--payload', payloadStr);
        }

        const env = { ...process.env, PYTHONUNBUFFERED: "1" };

        function trySpawn(index) {
            if (index >= pythonCandidates.length) {
                reject(new Error("No Python interpreter found"));
                return;
            }

            const python = pythonCandidates[index];
            const proc = spawn(python, cliArgs, {
                env,
                cwd: PROJECT_ROOT,
                stdio: ['ignore', 'pipe', 'pipe'],
                windowsHide: true,
            });

            let stdout = '';
            let stderr = '';
            let exited = false;

            proc.stdout.on('data', (d) => { stdout += d; });
            proc.stderr.on('data', (d) => { stderr += d; });

            proc.on('error', (err) => {
                if (exited) return;
                exited = true;
                if (err.code === 'ENOENT') {
                    // Try next candidate
                    trySpawn(index + 1);
                } else {
                    reject(err);
                }
            });

            proc.on('close', (code) => {
                if (exited) return;
                exited = true;
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error(`Python exited with code ${code}: ${stderr || stdout}`));
                }
            });
        }

        trySpawn(0);
    });
}

// ---------------------------------------------------------------------------
// Main dispatch
// ---------------------------------------------------------------------------

let initialized = false;

async function handleMessage(msg) {
    const method = msg?.method;
    const requestId = msg?.id;

    if (method === 'notifications/initialized') {
        initialized = true;
        return;
    }

    if (method === 'initialize') {
        sendMessage(handleInitialize(requestId, msg.params || {}));
        return;
    }

    if (!initialized && method !== undefined) {
        sendMessage(makeResponse(requestId, null, {
            code: -32002,
            message: "Server not initialized",
        }));
        return;
    }

    if (method === 'tools/list') {
        sendMessage(handleToolsList(requestId, msg.params || {}));
    } else if (method === 'tools/call') {
        const response = await handleToolsCall(requestId, msg.params || {});
        sendMessage(response);
    } else if (method !== undefined) {
        sendMessage(makeResponse(requestId, null, {
            code: -32601,
            message: `Method '${method}' not found`,
        }));
    }
}
