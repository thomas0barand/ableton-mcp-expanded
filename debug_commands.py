#!/usr/bin/env python3
"""
Debug script to test different commands
"""

import socket
import json

def test_command(command_type, params=None):
    """Test a specific command"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 9877))
            
            command = {
                "type": command_type,
                "params": params or {}
            }
            
            print(f"Sending command: {command}")
            sock.sendall(json.dumps(command).encode('utf-8'))
            response_data = sock.recv(8192)
            response = json.loads(response_data.decode('utf-8'))
            
            print(f"Response: {response}")
            return response
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing available commands...")
    
    # Test session info (known to work)
    print("\n1. Testing get_session_info:")
    test_command("get_session_info")
    
    # Test track info (known to work)
    print("\n2. Testing get_track_info:")
    test_command("get_track_info", {"track_index": 0})
    
    # Test device parameters (should work but doesn't)
    print("\n3. Testing get_device_parameters:")
    test_command("get_device_parameters", {"track_index": 0, "device_index": 1})
    
    # Test with different case
    print("\n4. Testing get_device_parameters (different case):")
    test_command("Get_Device_Parameters", {"track_index": 0, "device_index": 1})
    
    # Test with different spelling
    print("\n5. Testing get_device_params:")
    test_command("get_device_params", {"track_index": 0, "device_index": 1})
