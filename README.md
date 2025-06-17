# `CANtools`
### SocketCAN for the rest of us... 

<img src="https://github.com/slimelec/ollie-hw/blob/master/images/mpi_logo.png" width=300>

A comprehensive CAN bus interface tool for macOS that provides all the functionality of Linux SocketCAN utilities and more, designed to work with MEATPI devices and other SLCAN-compatible adapters.

## Table of Contents

- [Features](#features)
- [Hardware Overview](#hardware-overview)
- [Installation](#installation)
- [Device Setup](#device-setup)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Advanced Examples](#advanced-examples)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
- [Contributing](#contributing)

## Features

- **Complete SocketCAN equivalent** for macOS
- **Real-time statistics** and bus load monitoring
- **Message filtering** by ID, mask, or data patterns
- **Logging** in candump or CSV format with timestamps
- **Traffic replay** with speed control and looping
- **Traffic generation** with custom patterns and intervals
- **ISO-TP protocol support** for diagnostic communications
- **Live monitoring dashboard**
- **Automatic device detection** and symlink creation
- **Multiple UART interfaces** (RS232, RS485, UART A/B)
- **Professional CAN analysis tools**

## Hardware Overview

### Pinout

![Pinout Diagram](https://github.com/meatpiHQ/meatpi_ollie_v2/assets/94690098/30aeeb6b-d68a-4a25-8dac-d5ee201695c7)

### Device Interfaces

| Interface | Description | Device Path |
|-----------|-------------|-------------|
| CAN0 | Primary CAN interface | `/dev/cu.wchusbserial*1` |
| UART A | General purpose UART | `/dev/cu.wchusbserial*3` |
| UART B | General purpose UART | `/dev/cu.wchusbserial*5` |
| RS232 | RS232 serial interface | `/dev/cu.wchusbserial*7` |
| RS485 | RS485 serial interface | `/dev/cu.wchusbserial*9` |

**Note:** If the switch is set to VT then UARTA/B voltage must be set by target board. Otherwise VT pins will follow the voltage level set by the switch.

## Installation

### Prerequisites

Install python-can with serial support:

```bash
pipx install python-can
pipx inject python-can pyserial
```

### Download Tools

Download the complete toolset:

```bash
# Download main CAN tool
curl -O https://github.com/lukeswitz/meatpi_ollie_v2/raw/refs/heads/macOS/cantools.py
chmod +x cantools.py

# Download device setup script
curl -O https://github.com/lukeswitz/meatpi_ollie_v2/raw/refs/heads/macOS/setupOllieV2.py
chmod +x setupOllieV2.py

# Download cleanup script
curl -O https://github.com/lukeswitz/meatpi_ollie_v2/raw/refs/heads/macOS/cantoolsCleanup.py
chmod +x cantoolsCleanup.py
```

## Device Setup

### Automatic Setup

Run the device setup script to create convenient symlinks:

```bash
./setupOllieV2.py
```

This creates symbolic links in `~/meatpi-devices/`:
- `MEATPI-CAN0` → CAN interface
- `MEATPI-UARTA` → UART A
- `MEATPI-UARTB` → UART B  
- `MEATPI-RS232` → RS232
- `MEATPI-RS485` → RS485

### Manual Device Discovery

Find your device manually:

```bash
# List all USB serial devices
ls /dev/cu.*

# Find MEATPI devices specifically
ls -la ~/meatpi-devices/
```

### Cleanup

To remove all MEATPI setup:

```bash
./cantoolsCleanup.py
```

## Quick Start

### Test Connection

```bash
python3 cantools.py connect ~/meatpi-devices/MEATPI-CAN0
```

### Send a Message

```bash
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x123 DEADBEEF
```

### Listen for Messages

```bash
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0
```

## Command Reference

### Basic Operations

#### connect
Test connection to CAN device.

```bash
python3 cantools.py connect <device_path>
```

**Example:**
```bash
python3 cantools.py connect ~/meatpi-devices/MEATPI-CAN0
```

#### send
Send a single CAN message.

```bash
python3 cantools.py send <device> <id> <data> [options]
```

**Options:**
- `--extended` - Use extended 29-bit CAN ID
- `--rtr` - Send remote transmission request

**Examples:**
```bash
# Standard frame
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x123 DEADBEEF

# Extended frame
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x1FFFFFFF CAFEBABE --extended

# Remote transmission request
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x456 --rtr
```

#### listen
Listen for CAN messages with optional filtering and logging.

```bash
python3 cantools.py listen <device> [options]
```

**Options:**
- `--filter <id>` - Filter by CAN ID (hex)
- `--filter <id:mask>` - Filter with ID and mask
- `--log <file>` - Log messages to file
- `--csv` - Use CSV format for logging
- `--stats` - Show real-time statistics

**Examples:**
```bash
# Basic listening
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0

# Filter specific ID
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --filter 0x123

# Filter with mask (all IDs from 0x700-0x7FF)
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --filter 0x700:0x7F0

# Log to file with statistics
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --log session.log --stats

# Log to CSV format
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --log data.csv --csv
```

### Traffic Generation

#### generate
Generate repeated CAN traffic for testing.

```bash
python3 cantools.py generate <device> <id> <data> [options]
```

**Options:**
- `--interval <seconds>` - Time between messages (default: 0.1)
- `--count <number>` - Number of messages (default: infinite)

**Examples:**
```bash
# Generate 100 messages at 50ms intervals
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x123 CAFEBABE --interval 0.05 --count 100

# Continuous generation (Ctrl+C to stop)
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x456 FEEDFACE --interval 0.1
```

### Replay & Analysis

#### replay
Replay logged CAN sessions.

```bash
python3 cantools.py replay <device> <file> [options]
```

**Options:**
- `--speed <multiplier>` - Playback speed (default: 1.0)
- `--loop` - Loop playback continuously

**Examples:**
```bash
# Basic replay
python3 cantools.py replay ~/meatpi-devices/MEATPI-CAN0 session.log

# Replay at 2x speed with looping
python3 cantools.py replay ~/meatpi-devices/MEATPI-CAN0 session.csv --speed 2.0 --loop
```

#### sniffer
Real-time CAN bus monitoring dashboard.

```bash
python3 cantools.py sniffer <device>
```

**Example:**
```bash
python3 cantools.py sniffer ~/meatpi-devices/MEATPI-CAN0
```

### Diagnostic Communications

#### isotp
Send ISO-TP diagnostic messages.

```bash
python3 cantools.py isotp <device> <tx_id> <rx_id> <data>
```

**Example:**
```bash
# Request VIN from ECU
python3 cantools.py isotp ~/meatpi-devices/MEATPI-CAN0 0x7E0 0x7E8 0902
```

## Advanced Examples

### Multi-Terminal CAN Development

**Terminal 1 - Real-time monitoring:**
```bash
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 \
    --log session_$(date +%Y%m%d_%H%M%S).csv \
    --csv \
    --stats
```

**Terminal 2 - Send test messages:**
```bash
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x123 DEADBEEF
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x456 CAFEBABE
```

### Automotive ECU Testing

**Listen for diagnostic responses:**
```bash
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 \
    --filter 0x7E8:0x7F8 \
    --log ecu_responses.log \
    --stats
```

**Send diagnostic requests:**
```bash
# Request supported PIDs
python3 cantools.py isotp ~/meatpi-devices/MEATPI-CAN0 0x7E0 0x7E8 0100

# Request VIN
python3 cantools.py isotp ~/meatpi-devices/MEATPI-CAN0 0x7E0 0x7E8 0902

# Request engine RPM
python3 cantools.py isotp ~/meatpi-devices/MEATPI-CAN0 0x7E0 0x7E8 010C
```

### Traffic Analysis and Stress Testing

**Generate complex test patterns:**
```bash
# Background traffic generators
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x100 "11223344" --count 1000 --interval 0.01 &
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x200 "AABBCCDD" --count 500 --interval 0.02 &
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x300 "DEADBEEF" --count 200 --interval 0.05 &

# Monitor the chaos
python3 cantools.py sniffer ~/meatpi-devices/MEATPI-CAN0
```

### CAN Bus Reverse Engineering

**Capture and analyze unknown traffic:**
```bash
# Step 1: Capture all traffic
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 \
    --log unknown_device_$(date +%Y%m%d_%H%M%S).csv \
    --csv \
    --stats

# Step 2: Filter interesting IDs (after manual analysis)
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 \
    --filter 0x123 \
    --log filtered_analysis.csv \
    --csv

# Step 3: Replay captured traffic for testing
python3 cantools.py replay ~/meatpi-devices/MEATPI-CAN0 unknown_device_*.csv --speed 0.5
```

### Multi-Bus Setup

If you have multiple MEATPI devices:

```bash
# Bus 1 - Engine ECU
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 \
    --filter 0x7E0:0x7E8 \
    --log engine_bus.csv \
    --csv &

# Bus 2 - Body control
python3 cantools.py listen /dev/cu.wchusbserial87654321 \
    --filter 0x600:0x6FF \
    --log body_bus.csv \
    --csv &

# Monitor both
wait
```

## Linux SocketCAN Comparison

| Linux SocketCAN | macOS CAN Tool | Notes |
|----------------|----------------|-------|
| `slcand + ifconfig` | `connect` | Single command setup |
| `cansend` | `send` | Same functionality + extended frames |
| `candump` | `listen` | Plus filtering and statistics |
| `canplayer` | `replay` | Plus speed control and looping |
| `cangen` | `generate` | Plus custom patterns |
| `canbusload` | Built into `--stats` | Real-time monitoring |
| Multiple tools | Single tool | All features unified |

### Migration Examples

**Linux SocketCAN:**
```bash
slcand -o -s6 /dev/ttyUSB0 can0
ifconfig can0 up
candump can0
cansend can0 123#DEADBEEF
```

**macOS equivalent:**
```bash
python3 cantools.py connect ~/meatpi-devices/MEATPI-CAN0
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 &
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x123 DEADBEEF
```

## Troubleshooting

### Device Detection Issues

**Problem:** Device not found
```bash
# Check if device is connected
system_profiler SPUSBDataType | grep -A 10 -B 10 -i meatpi

# List all USB serial devices
ls /dev/cu.*

# Check for MEATPI devices specifically
ls /dev/cu.*wchusbserial*
```

**Problem:** Permission denied
```bash
# Check device permissions
ls -la /dev/cu.*wchusbserial*

# Add user to dialout group (if exists on macOS)
sudo dscl . -append /Groups/_developer GroupMembership $USER
```

### Connection Issues

**Problem:** Connection timeout
```bash
# Verify device path
python3 cantools.py connect /dev/cu.wchusbserial01234567891

# Try different baud rates (edit cantools.py if needed)
# Default is 500000, try 250000 or 125000
```

**Problem:** No messages received
```bash
# Check if device is in loopback mode
# Verify other end is transmitting
# Check bus termination (120Ω resistors)

# Send test message to verify TX works
python3 cantools.py send ~/meatpi-devices/MEATPI-CAN0 0x123 DEADBEEF

# Listen with verbose output
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --stats
```

### Performance Issues

**Problem:** High CPU usage
```bash
# Reduce message frequency
python3 cantools.py generate ~/meatpi-devices/MEATPI-CAN0 0x123 DEAD --interval 0.1

# Use filtering to reduce processing
python3 cantools.py listen ~/meatpi-devices/MEATPI-CAN0 --filter 0x100:0x700
```

**Problem:** Dropped messages
```bash
# Check bus load
python3 cantools.py sniffer ~/meatpi-devices/MEATPI-CAN0

# Increase buffer sizes (modify cantools.py)
# Reduce logging frequency
```

### Common Error Messages

**"Connection failed: [Errno 16] Device or resource busy"**
- Another application is using the device
- Kill other processes: `sudo pkill -f "cu.wchusbserial"`

**"Send failed: [Errno 5] Input/output error"**
- Device disconnected
- CAN bus not properly terminated
- Wrong baud rate

**"No module named 'can'"**
- Install python-can: `pipx install python-can`
- Install serial support: `pipx inject python-can pyserial`

## API Reference

### CANInterface Class

```python
from cantools import CANInterface

# Initialize
can_interface = CANInterface('/dev/cu.wchusbserial01234567891', bitrate=500000)

# Connect
if can_interface.connect():
    print("Connected successfully")

# Send message
can_interface.send_message(0x123, b'\xDE\xAD\xBE\xEF')

# Add filter
can_interface.add_filter(can_id=0x123, mask=0x7FF)

# Start logging
can_interface.start_logging('session.csv', format='csv')

# Listen for messages
can_interface.listen(show_stats=True)

# Generate traffic
can_interface.generate_traffic(0x456, b'\xCA\xFE\xBA\xBE', interval=0.1, count=100)

# ISO-TP communication
can_interface.isotp_send(0x7E0, 0x7E8, b'\x01\x00')

# Clean up
can_interface.close()
```

### Message Format

**Standard CAN Frame:**
```python
{
    'arbitration_id': 0x123,     # 11-bit ID
    'data': b'\xDE\xAD\xBE\xEF', # 0-8 bytes
    'is_extended_id': False,     # Standard frame
    'is_remote_frame': False     # Data frame
}
```

**Extended CAN Frame:**
```python
{
    'arbitration_id': 0x1FFFFFFF, # 29-bit ID
    'data': b'\xCA\xFE\xBA\xBE',  # 0-8 bytes
    'is_extended_id': True,       # Extended frame
    'is_remote_frame': False      # Data frame
}
```

### Logging Formats

**CSV Format:**
```csv
timestamp,id,dlc,data,extended,rtr
1640995200.123456,123,4,DEADBEEF,false,false
1640995200.223456,456,8,CAFEBABEFEEDFACE,false,false
```

**Candump Format:**
```
(1640995200.123456) MEATPI-CAN0 123 [4] DE AD BE EF
(1640995200.223456) MEATPI-CAN0 456 [8] CA FE BA BE FE ED FA CE
```

## Speed Reference

| Code | Bitrate | Common Use |
|------|---------|------------|
| s1 | 20 KBit | Low-speed automotive |
| s2 | 50 KBit | Industrial |
| s3 | 100 KBit | Building automation |
| s4 | 125 KBit | Automotive (low) |
| s5 | 250 KBit | Automotive (medium) |
| s6 | 500 KBit | Automotive (high) |
| s7 | 800 KBit | High-speed industrial |
| s8 | 1 MBit | Maximum speed |

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/lukeswitz/meatpi_ollie_v2.git
cd cantools

# Install development dependencies
pipx install python-can
pipx inject python-can pyserial pytest black flake8

# Run tests
python -m pytest tests/

# Format code
black cantools.py

# Lint code
flake8 cantools.py
```

### Adding Features

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Add tests for new functionality
4. Ensure all tests pass: `python -m pytest`
5. Format code: `black .`
6. Submit pull request

### Reporting Issues

Please include:
- macOS version
- Python version
- MEATPI device model
- Complete error messages
- Steps to reproduce

## License

MIT License - feel free to modify and distribute.

## Support

- **Documentation:** This README
- **Issues:** GitHub Issues
- **Discord:** [MeatPi Discord server](https://discord.gg/WXy8KQCE7V)
- **Funding:** [Crowd Supply](https://www.crowdsupply.com/meatpi-electronics/ollie-v2)
- **Website:** [www.meatpi.com](https://www.meatpi.com)

---

![MeatPi Logo](https://github.com/meatpiHQ/meatpi_ollie_v2/assets/94690098/50aeb7da-0b82-41b8-ae74-c0a40db11433)

**Made with ❤️ by the MeatPi team**
