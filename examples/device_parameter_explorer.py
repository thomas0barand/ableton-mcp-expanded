#!/usr/bin/env python3
"""
Device Parameter Explorer for Ableton MCP

This script helps you explore and control any device parameters in Ableton Live.
It provides a comprehensive interface to:
1. Browse tracks and devices
2. View all parameters for any device
3. Control parameters with various input methods
4. Save and load parameter presets

Usage:
    python device_parameter_explorer.py
"""

import socket
import json
import time
import sys
import os

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

def get_session_info():
    """Get current session information"""
    return send_command("get_session_info")

def get_track_info(track_index):
    """Get information about a specific track"""
    return send_command("get_track_info", {"track_index": track_index})

def get_device_parameters(track_index, device_index):
    """Get all parameters for a device"""
    return send_command("get_device_parameters", {
        "track_index": track_index,
        "device_index": device_index
    })

def set_parameter(track_index, device_index, param_index, value):
    """Set a single parameter value (0.0 to 1.0)"""
    return send_command("set_device_parameter", {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_index": param_index,
        "value": value
    })

def batch_set_parameters(track_index, device_index, param_indices, values):
    """Set multiple parameters at once"""
    return send_command("batch_set_device_parameters", {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_indices": param_indices,
        "values": values
    })

def browse_tracks():
    """Browse all tracks and their devices"""
    print("Session Overview")
    print("=" * 50)
    
    session = get_session_info()
    if not session:
        print("Failed to get session info")
        return None
    
    tracks = session.get("tracks", [])
    print(f"Tempo: {session.get('tempo', 'Unknown')} BPM")
    print(f"Tracks: {len(tracks)}")
    print()
    
    for i, track in enumerate(tracks):
        track_name = track.get("name", f"Track {i}")
        device_count = track.get("device_count", 0)
        print(f"[{i:2d}] {track_name:20s} ({device_count} devices)")
    
    return tracks

def browse_devices(track_index):
    """Browse devices on a specific track"""
    print(f"\nDevices on Track {track_index}")
    print("=" * 30)
    
    track_info = get_track_info(track_index)
    if not track_info:
        print("Failed to get track info")
        return None
    
    devices = track_info.get("devices", [])
    track_name = track_info.get("name", f"Track {track_index}")
    
    print(f"Track: {track_name}")
    print(f"Devices: {len(devices)}")
    print()
    
    for i, device in enumerate(devices):
        device_name = device.get("name", f"Device {i}")
        print(f"[{i:2d}] {device_name}")
    
    return devices

def display_parameters(track_index, device_index, parameters):
    """Display parameters in a formatted table"""
    if not parameters:
        print("No parameters found")
        return
    
    device_name = parameters[0].get("device_name", "Unknown Device") if parameters else "Unknown"
    track_name = parameters[0].get("track_name", f"Track {track_index}") if parameters else f"Track {track_index}"
    
    print(f"\nParameters for {device_name} on {track_name}")
    print("=" * 80)
    print(f"{'Idx':<4} {'Name':<25} {'Value':<10} {'Norm':<6} {'Range':<15} {'Status'}")
    print("-" * 80)
    
    for param in parameters:
        idx = param.get("index", "?")
        name = param.get("name", "Unknown")
        value = param.get("value", 0)
        norm_val = param.get("normalized_value", 0)
        min_val = param.get("min", 0)
        max_val = param.get("max", 1)
        enabled = param.get("is_enabled", True)
        
        status = "✓" if enabled else "✗"
        range_str = f"{min_val:.1f}-{max_val:.1f}"
        
        print(f"{idx:<4} {name:<25} {value:<10.3f} {norm_val:<6.3f} {range_str:<15} {status}")

def interactive_parameter_control(track_index, device_index, parameters):
    """Interactive parameter control interface"""
    print(f"\nInteractive Parameter Control")
    print("Commands:")
    print("  set <index> <value>        - Set parameter (0.0-1.0)")
    print("  batch <indices> <values>   - Set multiple parameters")
    print("  reset                      - Reset all parameters to 0.5")
    print("  random                     - Randomize all parameters")
    print("  save <filename>            - Save current state")
    print("  load <filename>            - Load saved state")
    print("  list                       - List all parameters")
    print("  back                       - Go back to device selection")
    print("  quit                       - Exit")
    print()
    
    while True:
        try:
            cmd = input("Param> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "quit":
                sys.exit(0)
            elif cmd[0] == "back":
                break
            elif cmd[0] == "list":
                display_parameters(track_index, device_index, parameters)
            elif cmd[0] == "set" and len(cmd) >= 3:
                param_idx = int(cmd[1])
                value = float(cmd[2])
                if not (0.0 <= value <= 1.0):
                    print("Value must be between 0.0 and 1.0")
                    continue
                result = set_parameter(track_index, device_index, param_idx, value)
                if result and "error" not in result:
                    print(f"✓ Set parameter {param_idx} to {value}")
                else:
                    print(f"✗ Error: {result.get('error', 'Unknown error')}")
            elif cmd[0] == "batch" and len(cmd) >= 3:
                try:
                    indices = [int(x) for x in cmd[1].split(',')]
                    values = [float(x) for x in cmd[2].split(',')]
                    if len(indices) != len(values):
                        print("Number of indices and values must match")
                        continue
                    for value in values:
                        if not (0.0 <= value <= 1.0):
                            print("All values must be between 0.0 and 1.0")
                            break
                    else:
                        result = batch_set_parameters(track_index, device_index, indices, values)
                        if result and "error" not in result:
                            print(f"✓ Set {len(indices)} parameters")
                        else:
                            print(f"✗ Error: {result.get('error', 'Unknown error')}")
                except ValueError:
                    print("Invalid format. Use: batch 0,1,2 0.5,0.7,0.3")
            elif cmd[0] == "reset":
                # Reset all parameters to 0.5
                indices = [p.get("index") for p in parameters if p.get("is_enabled", True)]
                values = [0.5] * len(indices)
                if indices:
                    result = batch_set_parameters(track_index, device_index, indices, values)
                    if result and "error" not in result:
                        print(f"✓ Reset {len(indices)} parameters to 0.5")
                    else:
                        print(f"✗ Error: {result.get('error', 'Unknown error')}")
            elif cmd[0] == "random":
                # Randomize all parameters
                import random
                indices = [p.get("index") for p in parameters if p.get("is_enabled", True)]
                values = [random.random() for _ in indices]
                if indices:
                    result = batch_set_parameters(track_index, device_index, indices, values)
                    if result and "error" not in result:
                        print(f"✓ Randomized {len(indices)} parameters")
                    else:
                        print(f"✗ Error: {result.get('error', 'Unknown error')}")
            elif cmd[0] == "save" and len(cmd) >= 2:
                filename = cmd[1]
                if not filename.endswith('.json'):
                    filename += '.json'
                save_preset(track_index, device_index, parameters, filename)
            elif cmd[0] == "load" and len(cmd) >= 2:
                filename = cmd[1]
                if not filename.endswith('.json'):
                    filename += '.json'
                load_preset(track_index, device_index, filename)
            else:
                print("Invalid command. Type 'quit' to exit.")
        except (ValueError, IndexError) as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def save_preset(track_index, device_index, parameters, filename):
    """Save current parameter state to a file"""
    try:
        preset = {
            "track_index": track_index,
            "device_index": device_index,
            "device_name": parameters[0].get("device_name", "Unknown") if parameters else "Unknown",
            "parameters": []
        }
        
        for param in parameters:
            if param.get("is_enabled", True):
                preset["parameters"].append({
                    "index": param.get("index"),
                    "name": param.get("name"),
                    "normalized_value": param.get("normalized_value", 0)
                })
        
        with open(filename, 'w') as f:
            json.dump(preset, f, indent=2)
        
        print(f"✓ Saved preset to {filename}")
    except Exception as e:
        print(f"✗ Error saving preset: {e}")

def load_preset(track_index, device_index, filename):
    """Load parameter state from a file"""
    try:
        with open(filename, 'r') as f:
            preset = json.load(f)
        
        if preset.get("track_index") != track_index or preset.get("device_index") != device_index:
            print(f"⚠ Preset is for track {preset.get('track_index')}, device {preset.get('device_index')}")
            confirm = input("Load anyway? (y/N): ").strip().lower()
            if confirm != 'y':
                return
        
        indices = []
        values = []
        
        for param in preset.get("parameters", []):
            indices.append(param["index"])
            values.append(param["normalized_value"])
        
        if indices:
            result = batch_set_parameters(track_index, device_index, indices, values)
            if result and "error" not in result:
                print(f"✓ Loaded preset from {filename}")
            else:
                print(f"✗ Error loading preset: {result.get('error', 'Unknown error')}")
        else:
            print("No parameters in preset file")
    except FileNotFoundError:
        print(f"✗ Preset file {filename} not found")
    except Exception as e:
        print(f"✗ Error loading preset: {e}")

def main():
    print("Ableton Device Parameter Explorer")
    print("=" * 40)
    
    # Check connection
    session = get_session_info()
    if not session:
        print("Failed to connect to Ableton MCP server.")
        print("Make sure Ableton Live is running with the Remote Script loaded.")
        return
    
    print("✓ Connected to Ableton Live")
    
    # Main navigation loop
    while True:
        try:
            # Browse tracks
            tracks = browse_tracks()
            if not tracks:
                break
            
            # Select track
            track_input = input(f"\nSelect track (0-{len(tracks)-1}) or 'quit': ").strip()
            if track_input.lower() == 'quit':
                break
            
            try:
                track_index = int(track_input)
                if not (0 <= track_index < len(tracks)):
                    print("Invalid track index")
                    continue
            except ValueError:
                print("Invalid input")
                continue
            
            # Browse devices on selected track
            while True:
                devices = browse_devices(track_index)
                if not devices:
                    break
                
                # Select device
                device_input = input(f"\nSelect device (0-{len(devices)-1}), 'back', or 'quit': ").strip()
                if device_input.lower() == 'quit':
                    sys.exit(0)
                elif device_input.lower() == 'back':
                    break
                
                try:
                    device_index = int(device_input)
                    if not (0 <= device_index < len(devices)):
                        print("Invalid device index")
                        continue
                except ValueError:
                    print("Invalid input")
                    continue
                
                # Get parameters and start control
                parameters = get_device_parameters(track_index, device_index)
                if parameters:
                    display_parameters(track_index, device_index, parameters)
                    interactive_parameter_control(track_index, device_index, parameters)
                else:
                    print("No parameters found for this device")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
