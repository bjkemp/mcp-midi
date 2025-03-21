"""
Tests for the MCP MIDI server
"""
import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.server import app


class TestMCPServer(unittest.TestCase):
    """Test cases for the MCP MIDI server"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    @patch('mido.open_output')
    @patch('rtmidi.MidiOut')
    def test_discover_midi_ports(self, mock_midi_out, mock_open_output):
        """Test discovering MIDI ports"""
        # Mock the MidiOut.get_ports() method
        mock_instance = mock_midi_out.return_value
        mock_instance.get_ports.return_value = ["Test MIDI Port 1", "Test MIDI Port 2"]
        
        # Make the request
        response = self.client.get("/midi/ports")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["ports"]), 2)
        self.assertEqual(data["ports"][0]["name"], "Test MIDI Port 1")
        self.assertEqual(data["ports"][1]["name"], "Test MIDI Port 2")
    
    @patch('mido.open_output')
    @patch('rtmidi.MidiOut')
    def test_connect_midi_port(self, mock_midi_out, mock_open_output):
        """Test connecting to a MIDI port"""
        # Mock the MidiOut.get_ports() method
        mock_instance = mock_midi_out.return_value
        mock_instance.get_ports.return_value = ["Test MIDI Port"]
        
        # Mock the open_output function
        mock_open_output.return_value = MagicMock()
        
        # Make the request
        response = self.client.post("/midi/connect/0")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Connected to MIDI port 0")
    
    @patch('mido.open_output')
    @patch('rtmidi.MidiOut')
    def test_note_on(self, mock_midi_out, mock_open_output):
        """Test sending a note_on message"""
        # Mock the MidiOut.get_ports() method
        mock_instance = mock_midi_out.return_value
        mock_instance.get_ports.return_value = ["Test MIDI Port"]
        
        # Mock the open_output function
        mock_port = MagicMock()
        mock_open_output.return_value = mock_port
        
        # Make the request
        response = self.client.post(
            "/midi/note_on",
            json={"note": 60, "velocity": 100, "channel": 0}
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        
        # Check that the port.send method was called
        mock_port.send.assert_called_once()
        args = mock_port.send.call_args[0]
        self.assertEqual(args[0].type, "note_on")
        self.assertEqual(args[0].note, 60)
        self.assertEqual(args[0].velocity, 100)
        self.assertEqual(args[0].channel, 0)
    
    @patch('mido.open_output')
    @patch('rtmidi.MidiOut')
    def test_mcp_endpoint_note_on(self, mock_midi_out, mock_open_output):
        """Test the MCP endpoint with a note_on message"""
        # Mock the MidiOut.get_ports() method
        mock_instance = mock_midi_out.return_value
        mock_instance.get_ports.return_value = ["Test MIDI Port"]
        
        # Mock the open_output function
        mock_port = MagicMock()
        mock_open_output.return_value = mock_port
        
        # Make the request
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "midi.note_on",
                "params": {
                    "note": 60,
                    "velocity": 100,
                    "channel": 0
                }
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "test-1")
        self.assertIn("result", data)
        
        # Check that the port.send method was called
        mock_port.send.assert_called_once()
        args = mock_port.send.call_args[0]
        self.assertEqual(args[0].type, "note_on")
        self.assertEqual(args[0].note, 60)
        self.assertEqual(args[0].velocity, 100)
        self.assertEqual(args[0].channel, 0)


if __name__ == "__main__":
    unittest.main()
