"""
Claude client for the MCP MIDI server
"""
import json
import logging
import re
import requests
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("claude_client")

# Regex pattern for MIDI command extraction
MIDI_COMMAND_PATTERN = r"```midi\s+(.*?)```"


class ClaudeClient:
    """Client for interacting with Claude via the MCP protocol"""
    
    def __init__(self, mcp_server_url: str = "http://127.0.0.1:8080"):
        """Initialize the Claude client
        
        Args:
            mcp_server_url: URL of the MCP MIDI server
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_endpoint = f"{mcp_server_url}/mcp"
        self.request_id = 0
    
    def extract_midi_commands(self, text: str) -> List[Dict[str, Any]]:
        """Extract MIDI commands from Claude's response
        
        Args:
            text: Claude's response text
            
        Returns:
            List of parsed MIDI commands
        """
        commands = []
        matches = re.finditer(MIDI_COMMAND_PATTERN, text, re.DOTALL)
        
        for match in matches:
            command_text = match.group(1).strip()
            try:
                command = json.loads(command_text)
                commands.append(command)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MIDI command: {e}")
                logger.debug(f"Command text: {command_text}")
        
        return commands
    
    def send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send an MCP request to the server
        
        Args:
            method: MCP method name
            params: MCP method parameters
            
        Returns:
            Server response
        """
        self.request_id += 1
        request_id = f"claude-{self.request_id}"
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        response = requests.post(self.mcp_endpoint, json=payload)
        return response.json()
    
    def process_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Process Claude's response and execute any MIDI commands
        
        Args:
            response_text: Claude's response text
            
        Returns:
            List of results from executed commands
        """
        commands = self.extract_midi_commands(response_text)
        results = []
        
        for cmd in commands:
            cmd_type = cmd.get("type", "")
            
            if cmd_type == "note_on":
                result = self.send_mcp_request("midi.note_on", {
                    "note": cmd.get("note"),
                    "velocity": cmd.get("velocity", 64),
                    "channel": cmd.get("channel", 0),
                    "port_id": cmd.get("port_id", 0)
                })
                results.append(result)
            
            elif cmd_type == "note_off":
                result = self.send_mcp_request("midi.note_off", {
                    "note": cmd.get("note"),
                    "velocity": cmd.get("velocity", 0),
                    "channel": cmd.get("channel", 0),
                    "port_id": cmd.get("port_id", 0)
                })
                results.append(result)
            
            elif cmd_type == "program_change":
                result = self.send_mcp_request("midi.program_change", {
                    "program": cmd.get("program", 0),
                    "channel": cmd.get("channel", 0),
                    "port_id": cmd.get("port_id", 0)
                })
                results.append(result)
            
            elif cmd_type == "control_change":
                result = self.send_mcp_request("midi.control_change", {
                    "control": cmd.get("control", 0),
                    "value": cmd.get("value", 0),
                    "channel": cmd.get("channel", 0),
                    "port_id": cmd.get("port_id", 0)
                })
                results.append(result)
            
            elif cmd_type == "discover":
                result = self.send_mcp_request("midi.discover", {})
                results.append(result)
            
            elif cmd_type == "connect":
                result = self.send_mcp_request("midi.connect", {
                    "port_id": cmd.get("port_id", 0)
                })
                results.append(result)
        
        return results
