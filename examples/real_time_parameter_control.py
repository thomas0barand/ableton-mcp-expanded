#!/usr/bin/env python3
"""
Real-time Parameter Control for Ableton MCP

This script demonstrates real-time parameter control using UDP for low-latency updates.
It's perfect for:
- MIDI controller mapping
- Touch/gesture control
- Real-time automation
- Live performance control

Usage:
    python real_time_parameter_control.py [track_index] [device_index] [param1] [param2]
    
Example:
    python real_time_parameter_control.py 0 0 0 1  # Control first two parameters of first device
"""

import socket
import json
import time
import sys
import threading
import math

# Configuration
TCP_HOST = "localhost"
TCP_PORT = 9877
UDP_HOST = "localhost"
UDP_PORT = 9878
BUFFER_SIZE = 8192

class RealTimeController:
    def __init__(self, track_index, device_index, param_indices):
        self.track_index = track_index
        self.device_index = device_index
        self.param_indices = param_indices
        self.udp_sock = None
        self.running = False
        self.parameter_names = {}
        
        # Initialize UDP socket
        try:
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"✓ UDP socket initialized for real-time control")
        except Exception as e:
            print(f"✗ Error initializing UDP socket: {e}")
            sys.exit(1)
    
    def send_tcp_command(self, command_type, params=None):
        """Send a command via TCP and return the response"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((TCP_HOST, TCP_PORT))
                
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
            print(f"TCP Error: {e}")
            return None
    
    def send_udp_parameter_update(self, param_index, value):
        """Send a parameter update via UDP (fire-and-forget)"""
        if not self.udp_sock:
            return
        
        message = {
            "type": "set_device_parameter",
            "params": {
                "track_index": self.track_index,
                "device_index": self.device_index,
                "parameter_index": param_index,
                "value": value
            }
        }
        
        try:
            payload = json.dumps(message).encode('utf-8')
            self.udp_sock.sendto(payload, (UDP_HOST, UDP_PORT))
        except Exception as e:
            print(f"UDP Error: {e}")
    
    def send_batch_udp_update(self, param_indices, values):
        """Send multiple parameter updates via UDP"""
        if not self.udp_sock:
            return
        
        message = {
            "type": "batch_set_device_parameters",
            "params": {
                "track_index": self.track_index,
                "device_index": self.device_index,
                "parameter_indices": param_indices,
                "values": values
            }
        }
        
        try:
            payload = json.dumps(message).encode('utf-8')
            self.udp_sock.sendto(payload, (UDP_HOST, UDP_PORT))
        except Exception as e:
            print(f"UDP Error: {e}")
    
    def get_device_info(self):
        """Get device and parameter information"""
        result = self.send_tcp_command("get_device_parameters", {
            "track_index": self.track_index,
            "device_index": self.device_index
        })
        
        if result:
            device_name = result.get("device_name", "Unknown Device")
            parameters = result.get("parameters", [])
            
            print(f"Device: {device_name}")
            print(f"Track: {result.get('track_name', f'Track {self.track_index}')}")
            print(f"Parameters: {len(parameters)}")
            print()
            
            # Store parameter names for display
            for param in parameters:
                idx = param.get("index")
                name = param.get("name", f"Param {idx}")
                self.parameter_names[idx] = name
                
                if idx in self.param_indices:
                    print(f"✓ [{idx:2d}] {name}")
            
            return parameters
        return []
    
    def keyboard_control(self):
        """Keyboard-based real-time control"""
        print("\nKeyboard Control Mode")
        print("Controls:")
        print("  Q/A - Parameter 0 down/up")
        print("  W/S - Parameter 1 down/up") 
        print("  E/D - Parameter 2 down/up")
        print("  R/F - Parameter 3 down/up")
        print("  T/G - Parameter 4 down/up")
        print("  SPACE - Reset all to 0.5")
        print("  ESC - Exit")
        print()
        
        # Current values
        values = [0.5] * len(self.param_indices)
        step_size = 0.05
        
        try:
            import msvcrt  # Windows
            use_msvcrt = True
        except ImportError:
            import tty, termios  # Unix
            use_msvcrt = False
        
        if not use_msvcrt:
            # Unix setup
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        
        try:
            while self.running:
                if use_msvcrt:
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                    else:
                        time.sleep(0.01)
                        continue
                else:
                    # Unix
                    key = sys.stdin.read(1).lower()
                
                if key == '\x1b':  # ESC
                    break
                elif key == ' ':
                    # Reset all to 0.5
                    values = [0.5] * len(self.param_indices)
                    self.send_batch_udp_update(self.param_indices, values)
                    self.display_values(values)
                elif key in 'qwert':
                    # Parameter controls
                    param_map = {'q': 0, 'w': 1, 'e': 2, 'r': 3, 't': 4}
                    if key in param_map and param_map[key] < len(self.param_indices):
                        param_idx = param_map[key]
                        values[param_idx] = max(0.0, values[param_idx] - step_size)
                        self.send_udp_parameter_update(self.param_indices[param_idx], values[param_idx])
                        self.display_values(values)
                elif key in 'asdfg':
                    # Parameter controls (up)
                    param_map = {'a': 0, 's': 1, 'd': 2, 'f': 3, 'g': 4}
                    if key in param_map and param_map[key] < len(self.param_indices):
                        param_idx = param_map[key]
                        values[param_idx] = min(1.0, values[param_idx] + step_size)
                        self.send_udp_parameter_update(self.param_indices[param_idx], values[param_idx])
                        self.display_values(values)
        
        finally:
            if not use_msvcrt:
                # Unix cleanup
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def display_values(self, values):
        """Display current parameter values"""
        print("\r" + " " * 80, end="")  # Clear line
        print(f"\rValues: ", end="")
        for i, (param_idx, value) in enumerate(zip(self.param_indices, values)):
            param_name = self.parameter_names.get(param_idx, f"P{param_idx}")
            print(f"{param_name}={value:.3f} ", end="")
        sys.stdout.flush()
    
    def sine_wave_demo(self, duration=10.0, frequency=0.5):
        """Demonstrate sine wave parameter modulation"""
        print(f"\nSine Wave Demo - {duration}s at {frequency}Hz")
        print("Press Ctrl+C to stop")
        
        start_time = time.time()
        try:
            while self.running and (time.time() - start_time) < duration:
                elapsed = time.time() - start_time
                
                # Generate sine wave values for each parameter
                values = []
                for i, param_idx in enumerate(self.param_indices):
                    # Offset each parameter by 90 degrees
                    phase = (elapsed * frequency * 2 * math.pi) + (i * math.pi / 2)
                    value = 0.5 + 0.5 * math.sin(phase)
                    values.append(value)
                
                # Send all parameters at once
                self.send_batch_udp_update(self.param_indices, values)
                self.display_values(values)
                
                time.sleep(0.02)  # 50 FPS
                
        except KeyboardInterrupt:
            print("\nDemo stopped")
    
    def random_walk_demo(self, duration=10.0, step_size=0.1):
        """Demonstrate random walk parameter modulation"""
        print(f"\nRandom Walk Demo - {duration}s")
        print("Press Ctrl+C to stop")
        
        import random
        start_time = time.time()
        values = [0.5] * len(self.param_indices)
        
        try:
            while self.running and (time.time() - start_time) < duration:
                # Random walk for each parameter
                for i in range(len(values)):
                    change = random.uniform(-step_size, step_size)
                    values[i] = max(0.0, min(1.0, values[i] + change))
                
                # Send all parameters at once
                self.send_batch_udp_update(self.param_indices, values)
                self.display_values(values)
                
                time.sleep(0.05)  # 20 FPS
                
        except KeyboardInterrupt:
            print("\nDemo stopped")
    
    def interactive_mode(self):
        """Interactive control mode"""
        print("\nInteractive Control Mode")
        print("Commands:")
        print("  keyboard - Keyboard control")
        print("  sine [duration] [freq] - Sine wave demo")
        print("  random [duration] - Random walk demo")
        print("  set <param> <value> - Set parameter directly")
        print("  reset - Reset all to 0.5")
        print("  quit - Exit")
        print()
        
        while self.running:
            try:
                cmd = input("RT> ").strip().split()
                if not cmd:
                    continue
                
                if cmd[0] == "quit":
                    break
                elif cmd[0] == "keyboard":
                    self.keyboard_control()
                elif cmd[0] == "sine":
                    duration = float(cmd[1]) if len(cmd) > 1 else 10.0
                    freq = float(cmd[2]) if len(cmd) > 2 else 0.5
                    self.sine_wave_demo(duration, freq)
                elif cmd[0] == "random":
                    duration = float(cmd[1]) if len(cmd) > 1 else 10.0
                    self.random_walk_demo(duration)
                elif cmd[0] == "set" and len(cmd) >= 3:
                    try:
                        param_idx = int(cmd[1])
                        value = float(cmd[2])
                        if 0 <= param_idx < len(self.param_indices) and 0.0 <= value <= 1.0:
                            self.send_udp_parameter_update(self.param_indices[param_idx], value)
                            print(f"Set parameter {param_idx} to {value}")
                        else:
                            print("Invalid parameter index or value")
                    except ValueError:
                        print("Invalid input")
                elif cmd[0] == "reset":
                    values = [0.5] * len(self.param_indices)
                    self.send_batch_udp_update(self.param_indices, values)
                    print("Reset all parameters to 0.5")
                else:
                    print("Unknown command")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
    
    def start(self):
        """Start the real-time controller"""
        self.running = True
        
        # Get device info
        parameters = self.get_device_info()
        if not parameters:
            print("Failed to get device parameters")
            return
        
        # Validate parameter indices
        valid_params = [p.get("index") for p in parameters if p.get("is_enabled", True)]
        self.param_indices = [idx for idx in self.param_indices if idx in valid_params]
        
        if not self.param_indices:
            print("No valid parameters found")
            return
        
        print(f"Controlling {len(self.param_indices)} parameters: {self.param_indices}")
        
        # Start interactive mode
        self.interactive_mode()
    
    def stop(self):
        """Stop the controller"""
        self.running = False
        if self.udp_sock:
            self.udp_sock.close()

def main():
    # Parse command line arguments
    if len(sys.argv) < 4:
        print("Usage: python real_time_parameter_control.py <track> <device> <param1> [param2] [param3] ...")
        print("Example: python real_time_parameter_control.py 0 0 0 1 2")
        sys.exit(1)
    
    track_index = int(sys.argv[1])
    device_index = int(sys.argv[2])
    param_indices = [int(x) for x in sys.argv[3:]]
    
    print(f"Real-time Parameter Control")
    print(f"Track: {track_index}, Device: {device_index}")
    print(f"Parameters: {param_indices}")
    print("=" * 40)
    
    controller = RealTimeController(track_index, device_index, param_indices)
    
    try:
        controller.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
