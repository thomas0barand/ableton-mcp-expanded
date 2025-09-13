#!/usr/bin/env python3
"""
Simple script to get EQ Eight parameters from Ableton Live
"""

import socket
import json

def send_command(command_type, params=None):
    """Send a command to the Ableton MCP server and return the response"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 9877))
            
            command = {
                "type": command_type,
                "params": params or {}
            }
            
            sock.sendall(json.dumps(command).encode('utf-8'))
            
            # Receive data in chunks until we get complete JSON
            chunks = []
            sock.settimeout(10.0)
            
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    
                    # Try to parse as JSON
                    data = b''.join(chunks)
                    try:
                        response = json.loads(data.decode('utf-8'))
                        break  # Successfully parsed, exit loop
                    except json.JSONDecodeError:
                        continue  # Incomplete JSON, keep receiving
                except socket.timeout:
                    break
            
            if not chunks:
                raise Exception("No data received")
            
            data = b''.join(chunks)
            response = json.loads(data.decode('utf-8'))
            
            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error"))
            
            return response.get("result", {})
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_device_parameters(track_index, device_index):
    """Get all parameters for a device"""
    print(f"Getting parameters for track {track_index}, device {device_index}...")
    result = send_command("get_device_parameters", {
        "track_index": track_index,
        "device_index": device_index
    })
    
    if result:
        device_name = result.get("device_name", "Unknown Device")
        parameters = result.get("parameters", [])
        
        print(f"\nDevice: {device_name}")
        print(f"Found {len(parameters)} parameters:")
        print("-" * 60)
        
        for param in parameters:
            idx = param.get("index", "?")
            name = param.get("name", "Unknown")
            value = param.get("value", 0)
            norm_val = param.get("normalized_value", 0)
            min_val = param.get("min", 0)
            max_val = param.get("max", 1)
            enabled = param.get("is_enabled", True)
            
            status = "✓" if enabled else "✗"
            print(f"{status} [{idx:2d}] {name:20s} = {value:8.3f} (norm: {norm_val:.3f}) [{min_val:.1f} - {max_val:.1f}]")
        
        return parameters
    return []

if __name__ == "__main__":
    # Get EQ Eight parameters (track 0, device 1)
    parameters = get_device_parameters(0, 1)
