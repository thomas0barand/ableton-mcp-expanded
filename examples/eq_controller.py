#!/usr/bin/env python3
"""
EQ Controller Example for Ableton MCP

This script demonstrates how to control EQ parameters in Ableton Live
using the MCP server. It shows how to:
1. Get device parameters for an EQ
2. Set individual EQ parameters
3. Batch set multiple parameters
4. Create automated EQ sweeps

Usage:
    python eq_controller.py [track_index] [device_index]
    
Example:
    python eq_controller.py 0 0  # Control first device on first track
"""

import socket
import json
import time
import sys
import math

# Configuration
HOST = "localhost"
PORT = 9877
BUFFER_SIZE = 8192

def send_command(command_type, params=None):
    """Send a command to the Ableton MCP server and return the response"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            
            command = {
                "type": command_type,
                "params": params or {}
            }
            
            sock.sendall(json.dumps(command).encode('utf-8'))
            response_data = sock.recv(BUFFER_SIZE)
            response = json.loads(response_data.decode('utf-8'))
            
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

def set_parameter(track_index, device_index, param_index, value):
    """Set a single parameter value (0.0 to 1.0)"""
    result = send_command("set_device_parameter", {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_index": param_index,
        "value": value
    })
    
    if result and "error" not in result:
        param_name = result.get("parameter_name", f"Parameter {param_index}")
        actual_value = result.get("value", "unknown")
        print(f"Set {param_name} to {actual_value} (normalized: {value})")
        return True
    else:
        print(f"Error setting parameter: {result.get('error', 'Unknown error')}")
        return False

def batch_set_parameters(track_index, device_index, param_indices, values):
    """Set multiple parameters at once"""
    result = send_command("batch_set_device_parameters", {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_indices": param_indices,
        "values": values
    })
    
    if result and "error" not in result:
        updated_count = result.get("updated_parameters_count", 0)
        details = result.get("details", [])
        param_names = [p.get("name", f"Param {p.get('index', '?')}") for p in details]
        print(f"Successfully set {updated_count} parameters: {', '.join(param_names)}")
        return True
    else:
        print(f"Error setting parameters: {result.get('error', 'Unknown error')}")
        return False

def eq_sweep_demo(track_index, device_index, param_index, duration=5.0, steps=50):
    """Create an automated sweep of an EQ parameter"""
    print(f"\nCreating EQ sweep for parameter {param_index} over {duration} seconds...")
    
    step_delay = duration / steps
    
    for i in range(steps + 1):
        # Create a sine wave sweep from 0 to 1 and back
        progress = i / steps
        value = 0.5 + 0.5 * math.sin(progress * 2 * math.pi)
        
        if set_parameter(track_index, device_index, param_index, value):
            print(f"Step {i:2d}/{steps}: {value:.3f}", end='\r')
            time.sleep(step_delay)
        else:
            break
    
    print(f"\nEQ sweep completed!")

def interactive_control(track_index, device_index, parameters):
    """Interactive parameter control"""
    print(f"\nInteractive Control Mode")
    print("Commands:")
    print("  set <param_index> <value>  - Set parameter (0.0-1.0)")
    print("  batch <indices> <values>   - Set multiple parameters")
    print("  sweep <param_index>        - Create parameter sweep")
    print("  list                       - List all parameters")
    print("  quit                       - Exit")
    print()
    
    while True:
        try:
            cmd = input("EQ> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "quit":
                break
            elif cmd[0] == "list":
                for param in parameters:
                    idx = param.get("index", "?")
                    name = param.get("name", "Unknown")
                    norm_val = param.get("normalized_value", 0)
                    print(f"  [{idx:2d}] {name:20s} = {norm_val:.3f}")
            elif cmd[0] == "set" and len(cmd) >= 3:
                param_idx = int(cmd[1])
                value = float(cmd[2])
                set_parameter(track_index, device_index, param_idx, value)
            elif cmd[0] == "batch" and len(cmd) >= 3:
                # Parse indices and values
                indices = [int(x) for x in cmd[1].split(',')]
                values = [float(x) for x in cmd[2].split(',')]
                batch_set_parameters(track_index, device_index, indices, values)
            elif cmd[0] == "sweep" and len(cmd) >= 2:
                param_idx = int(cmd[1])
                duration = float(cmd[2]) if len(cmd) > 2 else 5.0
                eq_sweep_demo(track_index, device_index, param_idx, duration)
            else:
                print("Invalid command. Type 'quit' to exit.")
        except (ValueError, IndexError) as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

def main():
    # Parse command line arguments
    track_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    device_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"EQ Controller - Track {track_index}, Device {device_index}")
    print("=" * 50)
    
    # Get device parameters
    parameters = get_device_parameters(track_index, device_index)
    
    if not parameters:
        print("No parameters found or error occurred.")
        return
    
    # Check if this looks like an EQ device
    device_name = parameters[0].get("device_name", "").lower() if parameters else ""
    if "eq" in device_name or "filter" in device_name:
        print(f"\n✓ Detected EQ/Filter device: {device_name}")
    else:
        print(f"\n⚠ Device '{device_name}' may not be an EQ")
    
    # Start interactive control
    interactive_control(track_index, device_index, parameters)

if __name__ == "__main__":
    main()
