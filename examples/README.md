# Device Parameter Control Examples

This directory contains example scripts demonstrating how to control device parameters in Ableton Live using the MCP server.

## Prerequisites

1. **Ableton Live** with the Remote Script loaded
2. **MCP Server** running (`python -m MCP_Server.server`)
3. **Python 3.7+** with required dependencies

## Available Examples

### 1. EQ Controller (`eq_controller.py`)

A specialized controller for EQ and filter devices with interactive controls and automated sweeps.

**Features:**
- Browse and display EQ parameters
- Interactive parameter control
- Automated parameter sweeps
- Batch parameter setting

**Usage:**
```bash
python eq_controller.py [track_index] [device_index]
```

**Example:**
```bash
# Control first device on first track
python eq_controller.py 0 0

# Interactive commands:
EQ> set 0 0.7          # Set parameter 0 to 0.7
EQ> batch 0,1,2 0.5,0.3,0.8  # Set multiple parameters
EQ> sweep 0            # Create parameter sweep
EQ> list               # List all parameters
```

### 2. Device Parameter Explorer (`device_parameter_explorer.py`)

A comprehensive tool for exploring and controlling any device parameters in Ableton Live.

**Features:**
- Browse tracks and devices
- View all parameters with detailed info
- Interactive parameter control
- Save/load parameter presets
- Batch operations
- Random parameter generation

**Usage:**
```bash
python device_parameter_explorer.py
```

**Example Workflow:**
1. Select a track from the list
2. Select a device on that track
3. View all parameters with their current values
4. Use interactive commands to control parameters
5. Save presets for later use

### 3. Real-time Parameter Control (`real_time_parameter_control.py`)

High-performance real-time parameter control using UDP for low-latency updates.

**Features:**
- UDP-based real-time updates
- Keyboard control
- Sine wave modulation
- Random walk patterns
- Batch parameter updates

**Usage:**
```bash
python real_time_parameter_control.py [track_index] [device_index] [param1] [param2] ...
```

**Example:**
```bash
# Control first two parameters of first device
python real_time_parameter_control.py 0 0 0 1

# Interactive commands:
RT> keyboard           # Start keyboard control
RT> sine 10 0.5        # 10-second sine wave at 0.5Hz
RT> random 5           # 5-second random walk
RT> set 0 0.8          # Set parameter 0 to 0.8
```

## Parameter Value System

All parameter values use **normalized ranges** (0.0 to 1.0):
- `0.0` = Minimum value
- `0.5` = Middle value  
- `1.0` = Maximum value

The MCP server automatically converts these to the actual parameter ranges in Ableton Live.

## Common Device Types

### EQ Eight
- **Parameter 0**: High Freq (0.0-1.0)
- **Parameter 1**: High Gain (0.0-1.0)
- **Parameter 2**: Mid Freq (0.0-1.0)
- **Parameter 3**: Mid Gain (0.0-1.0)
- **Parameter 4**: Mid Q (0.0-1.0)
- **Parameter 5**: Low Freq (0.0-1.0)
- **Parameter 6**: Low Gain (0.0-1.0)
- **Parameter 7**: Low Q (0.0-1.0)

### Auto Filter
- **Parameter 0**: Frequency (0.0-1.0)
- **Parameter 1**: Resonance (0.0-1.0)
- **Parameter 2**: Envelope (0.0-1.0)
- **Parameter 3**: LFO Amount (0.0-1.0)
- **Parameter 4**: LFO Rate (0.0-1.0)

### Compressor
- **Parameter 0**: Threshold (0.0-1.0)
- **Parameter 1**: Ratio (0.0-1.0)
- **Parameter 2**: Attack (0.0-1.0)
- **Parameter 3**: Release (0.0-1.0)
- **Parameter 4**: Makeup (0.0-1.0)

## Advanced Usage

### Creating Custom Controllers

You can create your own parameter controllers by using the MCP tools:

```python
import socket
import json

def send_command(command_type, params=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 9877))
        command = {"type": command_type, "params": params or {}}
        sock.sendall(json.dumps(command).encode('utf-8'))
        response = json.loads(sock.recv(8192).decode('utf-8'))
        return response.get("result", {})

# Get device parameters
params = send_command("get_device_parameters", {
    "track_index": 0,
    "device_index": 0
})

# Set a parameter
result = send_command("set_device_parameter", {
    "track_index": 0,
    "device_index": 0,
    "parameter_index": 0,
    "value": 0.7
})
```

### UDP for Real-time Control

For high-frequency parameter updates, use UDP:

```python
import socket
import json

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_parameter_update(track, device, param, value):
    message = {
        "type": "set_device_parameter",
        "params": {
            "track_index": track,
            "device_index": device,
            "parameter_index": param,
            "value": value
        }
    }
    udp_sock.sendto(json.dumps(message).encode('utf-8'), ("localhost", 9878))

# Send real-time updates
send_parameter_update(0, 0, 0, 0.5)
```

## Troubleshooting

### Connection Issues
- Ensure Ableton Live is running
- Check that the Remote Script is loaded
- Verify the MCP server is running on port 9877
- Check firewall settings

### Parameter Control Issues
- Verify track and device indices are correct
- Check that parameters are enabled
- Ensure values are between 0.0 and 1.0
- Check Ableton Live's device parameter ranges

### Performance Issues
- Use UDP for high-frequency updates
- Batch multiple parameter changes
- Reduce update frequency if needed
- Check system resources

## Tips and Best Practices

1. **Start Simple**: Begin with basic parameter control before advanced features
2. **Use Batch Updates**: Set multiple parameters at once for better performance
3. **Validate Inputs**: Always check parameter ranges and device availability
4. **Handle Errors**: Implement proper error handling for robust applications
5. **Test Thoroughly**: Verify parameter changes in Ableton Live
6. **Document Presets**: Save parameter states for easy recall
7. **Monitor Performance**: Watch for latency and update frequency issues

## Integration Examples

### MIDI Controller Integration
```python
# Map MIDI CC to parameters
def on_midi_cc(cc_number, value):
    param_map = {1: 0, 2: 1, 3: 2}  # CC to parameter mapping
    if cc_number in param_map:
        normalized_value = value / 127.0
        send_parameter_update(0, 0, param_map[cc_number], normalized_value)
```

### Touch/Gesture Control
```python
# Map touch coordinates to parameters
def on_touch(x, y, width, height):
    param_x = x / width
    param_y = y / height
    send_batch_parameter_update(0, 0, [0, 1], [param_x, param_y])
```

### Automation Recording
```python
# Record parameter changes over time
def record_automation(duration, callback):
    start_time = time.time()
    while time.time() - start_time < duration:
        values = callback(time.time() - start_time)
        send_batch_parameter_update(0, 0, param_indices, values)
        time.sleep(0.02)  # 50 FPS
```
