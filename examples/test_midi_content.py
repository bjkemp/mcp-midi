
import requests
import json
import time

# Base URL of the MCP-MIDI server
BASE_URL = "http://localhost:8080"

# The base64-encoded MIDI data from our generate_midi.py script
MIDI_DATA = """TVRoZAAAAAYAAQACAeBNVHJrAAAAPQDAOACQQ2SBcIBDQACQQ2SBcIBDQACQRWSDYIBFQACQQ2SDYIBDQACQSGSDYIBIQACQR2SHQIBHQAD/LwBNVHJrAAAAbwCZJGQKiSQAgWaZKlAKiSoAgWaZKjwKiSoAg2CZJGQKiSQAgWaZKlAKiSoAgWaZJmQKiSYAg2CZJGQKiSQAgWaZKlAKiSoAgWaZKjwKiSoAg2CZJGQKiSQAgWaZKlAKiSoAgWaZJmQKiSYAAP8vAA=="""

def main():
    # Step 1: Check if the server is running
    try:
        response = requests.get(f"{BASE_URL}/midi/ports")
        if response.status_code != 200:
            print("Server not responding correctly. Is it running?")
            return
        
        ports = response.json().get("ports", [])
        if not ports:
            print("No MIDI ports found. Is a MIDI device connected?")
            return
        
        print(f"Found {len(ports)} MIDI ports: {ports}")
        
        # Step 2: Connect to the first available MIDI port
        port_id = ports[0]["id"]
        response = requests.post(f"{BASE_URL}/midi/connect/{port_id}")
        if response.status_code != 200:
            print(f"Failed to connect to MIDI port {port_id}")
            return
        
        print(f"Connected to MIDI port {port_id}")
        
        # Step 3: Load the MIDI content
        payload = {
            "data": MIDI_DATA,
            "name": "Happy Birthday"
        }
        
        response = requests.post(f"{BASE_URL}/midi/load_content", json=payload)
        if response.status_code != 200:
            print(f"Failed to load MIDI content: {response.text}")
            return
        
        print(f"Loaded MIDI content: {response.json()}")
        
        # Step 4: Play the MIDI file
        payload = {
            "name": "Happy Birthday",
            "port_id": port_id
        }
        
        response = requests.post(f"{BASE_URL}/midi/play_file", json=payload)
        if response.status_code != 200:
            print(f"Failed to play MIDI file: {response.text}")
            return
        
        print(f"Playing MIDI file: {response.json()}")
        
        # Wait for the music to finish (approximately)
        print("Waiting for the music to finish...")
        time.sleep(10)
        
        # Step 5: Stop any remaining notes
        response = requests.post(f"{BASE_URL}/midi/all_notes_off")
        
        print("Test completed successfully!")
    
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
