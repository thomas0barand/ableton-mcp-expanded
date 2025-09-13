#!/usr/bin/env python3
"""
Script to get EQ Eight parameters using direct TCP connection
This can be used as a workaround until MCP tools are properly working
"""

import socket
import json

def get_device_parameters(track_index, device_index):
    """Get all parameters for a device using direct TCP connection"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 9877))
            
            command = {
                "type": "get_device_parameters",
                "params": {"track_index": track_index, "device_index": device_index}
            }
            
            sock.sendall(json.dumps(command).encode('utf-8'))
            
            # Read response in chunks
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            if response.get('status') == 'success':
                return response.get('result', {})
            else:
                print(f"Error: {response.get('message', 'Unknown error')}")
                return {}
                
    except Exception as e:
        print(f"Error: {e}")
        return {}

def set_device_parameter(track_index, device_index, parameter_index, value):
    """Set a device parameter using direct TCP connection"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 9877))
            
            command = {
                "type": "set_device_parameter",
                "params": {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter_index": parameter_index,
                    "value": value
                }
            }
            
            sock.sendall(json.dumps(command).encode('utf-8'))
            response_data = sock.recv(8192)
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get('status') == 'success':
                return response.get('result', {})
            else:
                print(f"Error: {response.get('message', 'Unknown error')}")
                return {}
                
    except Exception as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    # Get EQ Eight parameters (track 0, device 1)
    print("Getting EQ Eight parameters...")
    result = get_device_parameters(0, 1)
    
    if result:
        device_name = result.get('device_name', 'Unknown Device')
        parameters = result.get('parameters', [])
        
        print(f"\nDevice: {device_name}")
        print(f"Found {len(parameters)} parameters:")
        print("-" * 60)
        
        for param in parameters:
            idx = param.get('index', '?')
            name = param.get('name', 'Unknown')
            value = param.get('value', 0)
            norm_val = param.get('normalized_value', 0)
            min_val = param.get('min', 0)
            max_val = param.get('max', 1)
            enabled = param.get('is_enabled', True)
            
            status = '✓' if enabled else '✗'
            print(f"{status} [{idx:2d}] {name:20s} = {value:8.3f} (norm: {norm_val:.3f}) [{min_val:.1f} - {max_val:.1f}]")
    else:
        print("Failed to get device parameters")
