"""
Tests for the Claude client
"""
import json
import unittest
from unittest.mock import MagicMock, patch

from src.claude_client import ClaudeClient


class TestClaudeClient(unittest.TestCase):
    """Test cases for the Claude client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = ClaudeClient("http://localhost:8080")
    
    def test_extract_midi_commands_single(self):
        """Test extracting a single MIDI command"""
        text = """
        Here's a MIDI command to play middle C:
        
        ```midi
        {
          "type": "note_on",
          "note": 60,
          "velocity": 100,
          "channel": 0
        }
        ```
        """
        
        commands = self.client.extract_midi_commands(text)
        
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["type"], "note_on")
        self.assertEqual(commands[0]["note"], 60)
        self.assertEqual(commands[0]["velocity"], 100)
        self.assertEqual(commands[0]["channel"], 0)
    
    def test_extract_midi_commands_multiple(self):
        """Test extracting multiple MIDI commands"""
        text = """
        Here's a sequence of notes:
        
        ```midi
        {
          "type": "note_on",
          "note": 60,
          "velocity": 100,
          "channel": 0
        }
        ```
        
        And now turn it off:
        
        ```midi
        {
          "type": "note_off",
          "note": 60,
          "channel": 0
        }
        ```
        """
        
        commands = self.client.extract_midi_commands(text)
        
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0]["type"], "note_on")
        self.assertEqual(commands[1]["type"], "note_off")
    
    def test_extract_midi_commands_invalid_json(self):
        """Test extracting an invalid MIDI command"""
        text = """
        This is an invalid command:
        
        ```midi
        {
          "type": "note_on",
          "note": 60,
          missing a closing brace
        ```
        """
        
        commands = self.client.extract_midi_commands(text)
        
        self.assertEqual(len(commands), 0)
    
    @patch('requests.post')
    def test_send_mcp_request(self, mock_post):
        """Test sending an MCP request"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "claude-1",
            "result": {"message": "Note on: 60, velocity: 100"}
        }
        mock_post.return_value = mock_response
        
        # Send the request
        result = self.client.send_mcp_request("midi.note_on", {
            "note": 60,
            "velocity": 100,
            "channel": 0
        })
        
        # Check the result
        self.assertEqual(result["result"]["message"], "Note on: 60, velocity: 100")
        
        # Check that post was called with the right arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:8080/mcp")
        self.assertEqual(kwargs["json"]["method"], "midi.note_on")
    
    @patch.object(ClaudeClient, 'send_mcp_request')
    def test_process_claude_response(self, mock_send_mcp_request):
        """Test processing a Claude response"""
        # Mock the response
        mock_send_mcp_request.return_value = {
            "jsonrpc": "2.0",
            "id": "claude-1",
            "result": {"message": "Note on: 60, velocity: 100"}
        }
        
        # Process the response
        text = """
        Let me play a C major chord:
        
        ```midi
        {
          "type": "note_on",
          "note": 60,
          "velocity": 100,
          "channel": 0
        }
        ```
        
        ```midi
        {
          "type": "note_on",
          "note": 64,
          "velocity": 100,
          "channel": 0
        }
        ```
        
        ```midi
        {
          "type": "note_on",
          "note": 67,
          "velocity": 100,
          "channel": 0
        }
        ```
        """
        
        results = self.client.process_claude_response(text)
        
        # Check that send_mcp_request was called 3 times
        self.assertEqual(mock_send_mcp_request.call_count, 3)
        
        # Check the methods and params
        calls = mock_send_mcp_request.call_args_list
        self.assertEqual(calls[0][0][0], "midi.note_on")
        self.assertEqual(calls[0][0][1]["note"], 60)
        
        self.assertEqual(calls[1][0][0], "midi.note_on")
        self.assertEqual(calls[1][0][1]["note"], 64)
        
        self.assertEqual(calls[2][0][0], "midi.note_on")
        self.assertEqual(calls[2][0][1]["note"], 67)


if __name__ == "__main__":
    unittest.main()
