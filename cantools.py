#!/usr/bin/env python3
import can
import time
import sys
import threading
import json
import csv
import signal
from datetime import datetime
from queue import Queue, Empty
from collections import defaultdict, deque
import statistics
import re

class CANInterface:
    def __init__(self, device_path, bitrate=500000):
        self.device_path = device_path
        self.bitrate = bitrate
        self.bus = None
        self.running = False
        self.stats = defaultdict(lambda: {'count': 0, 'last_seen': None, 'intervals': deque(maxlen=100)})
        self.filters = []
        self.log_file = None
        self.replay_messages = []
        
    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface='slcan',
                channel=self.device_path,
                bitrate=self.bitrate
            )
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_message(self, can_id, data, extended=False, rtr=False):
        if not self.bus:
            return False
            
        try:
            if isinstance(data, str):
                data = bytes.fromhex(data.replace('#', '').replace(' ', ''))
            
            msg = can.Message(
                arbitration_id=can_id, 
                data=data,
                is_extended_id=extended,
                is_remote_frame=rtr
            )
            self.bus.send(msg)
            
            # Fix the f-string formatting
            if extended:
                id_str = f"{can_id:08X}"
            else:
                id_str = f"{can_id:03X}"
            
            print(f"TX: {id_str} [{len(data)}] {data.hex().upper()}")
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def add_filter(self, can_id=None, mask=None, data_pattern=None):
        self.filters.append({
            'id': can_id,
            'mask': mask,
            'data': data_pattern
        })
    
    def message_matches_filters(self, msg):
        if not self.filters:
            return True
            
        for f in self.filters:
            if f['id'] is not None:
                if f['mask']:
                    if (msg.arbitration_id & f['mask']) != (f['id'] & f['mask']):
                        continue
                else:
                    if msg.arbitration_id != f['id']:
                        continue
            
            if f['data'] and f['data'] not in msg.data.hex():
                continue
                
            return True
        return False
    
    def start_logging(self, filename, format='candump'):
        if format == 'csv':
            self.log_file = open(filename, 'w', newline='')
            writer = csv.writer(self.log_file)
            writer.writerow(['timestamp', 'id', 'dlc', 'data', 'extended', 'rtr'])
        else:
            self.log_file = open(filename, 'w')
    
    def log_message(self, msg, format='candump'):
        if not self.log_file:
            return
            
        timestamp = time.time()
        if format == 'csv':
            writer = csv.writer(self.log_file)
            if msg.is_extended_id:
                id_str = f"{msg.arbitration_id:08X}"
            else:
                id_str = f"{msg.arbitration_id:03X}"
            
            writer.writerow([
                timestamp,
                id_str,
                len(msg.data),
                msg.data.hex().upper(),
                msg.is_extended_id,
                msg.is_remote_frame
            ])
        else:
            ts_str = f"({timestamp:.6f})"
            if msg.is_extended_id:
                id_str = f"{msg.arbitration_id:08X}"
            else:
                id_str = f"{msg.arbitration_id:03X}"
            
            data_str = ' '.join([f'{b:02X}' for b in msg.data])
            self.log_file.write(f"{ts_str} MEATPI-CAN0 {id_str} [{len(msg.data)}] {data_str}\n")
        
        self.log_file.flush()
    
    def update_stats(self, msg):
        now = time.time()
        id_key = msg.arbitration_id
        
        if self.stats[id_key]['last_seen']:
            interval = now - self.stats[id_key]['last_seen']
            self.stats[id_key]['intervals'].append(interval)
        
        self.stats[id_key]['count'] += 1
        self.stats[id_key]['last_seen'] = now
    
    def get_bus_load(self, window_seconds=1.0):
        now = time.time()
        recent_count = sum(1 for stat in self.stats.values() 
                          if stat['last_seen'] and (now - stat['last_seen']) < window_seconds)
        
        theoretical_max = self.bitrate / 64  # Rough estimate
        return (recent_count / theoretical_max) * 100 if theoretical_max > 0 else 0
    
    def listen(self, show_stats=False, log_format='candump'):
        if not self.bus:
            return
            
        self.running = True
        print("RX: Listening... (Ctrl+C to stop)")
        
        last_stats_time = time.time()
        
        try:
            for message in self.bus:
                if not self.running:
                    break
                
                if not self.message_matches_filters(message):
                    continue
                
                self.update_stats(message)
                
                if self.log_file:
                    self.log_message(message, log_format)
                
                if message.is_extended_id:
                    id_str = f"{message.arbitration_id:08X}"
                else:
                    id_str = f"{message.arbitration_id:03X}"
                
                data_str = ' '.join([f'{b:02X}' for b in message.data])
                flags = ""
                if message.is_extended_id:
                    flags += "X"
                if message.is_remote_frame:
                    flags += "R"
                
                print(f"RX: {id_str} [{len(message.data)}] {data_str} {flags}")
                
                if show_stats and time.time() - last_stats_time > 5:
                    self.print_stats()
                    last_stats_time = time.time()
                
        except KeyboardInterrupt:
            print("\nStopped")
        finally:
            self.running = False
    
    def print_stats(self):
        print("\n--- Statistics ---")
        print(f"Bus load: {self.get_bus_load():.1f}%")
        print("ID       Count    Avg Interval")
        
        sorted_stats = sorted(self.stats.items(), key=lambda x: x[1]['count'], reverse=True)
        for can_id, stat in sorted_stats[:10]:
            avg_interval = statistics.mean(stat['intervals']) if stat['intervals'] else 0
            print(f"{can_id:08X} {stat['count']:8d} {avg_interval*1000:8.1f}ms")
        print("--- End Stats ---\n")
    
    def replay(self, filename, speed=1.0, loop=False):
        try:
            with open(filename, 'r') as f:
                if filename.endswith('.csv'):
                    reader = csv.DictReader(f)
                    messages = []
                    for row in reader:
                        messages.append({
                            'id': int(row['id'], 16),
                            'data': bytes.fromhex(row['data']),
                            'extended': row['extended'].lower() == 'true',
                            'timestamp': float(row['timestamp'])
                        })
                else:
                    # Parse candump format
                    messages = []
                    for line in f:
                        if match := re.match(r'\(([\d.]+)\).*?([A-F0-9]+)\s+\[(\d+)\]\s+([A-F0-9\s]+)', line):
                            timestamp, can_id, dlc, data = match.groups()
                            messages.append({
                                'id': int(can_id, 16),
                                'data': bytes.fromhex(data.replace(' ', '')),
                                'extended': len(can_id) > 3,
                                'timestamp': float(timestamp)
                            })
            
            if not messages:
                print("No messages found in file")
                return
            
            base_time = messages[0]['timestamp']
            start_time = time.time()
            
            while True:
                for msg in messages:
                    if not self.running:
                        return
                    
                    target_time = start_time + (msg['timestamp'] - base_time) / speed
                    sleep_time = target_time - time.time()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                    self.send_message(msg['id'], msg['data'], msg['extended'])
                
                if not loop:
                    break
                    
                print("Looping replay...")
                start_time = time.time()
                
        except FileNotFoundError:
            print(f"File {filename} not found")
        except Exception as e:
            print(f"Replay failed: {e}")
    
    def generate_traffic(self, can_id, data_generator, interval=0.1, count=None):
        sent = 0
        try:
            while self.running and (count is None or sent < count):
                if callable(data_generator):
                    data = data_generator()
                else:
                    data = data_generator
                
                self.send_message(can_id, data)
                sent += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\nGenerated {sent} messages")
    
    def isotp_send(self, tx_id, rx_id, data, timeout=5.0):
        """ISO-TP single/multi-frame transmission"""
        if len(data) <= 7:
            # Single frame
            sf_data = bytes([len(data)]) + data
            self.send_message(tx_id, sf_data)
            print(f"ISO-TP SF: {tx_id:03X} -> {len(data)} bytes")
        else:
            # Multi-frame
            frames = []
            payload = data
            
            # First frame
            ff_data = bytes([0x10 | ((len(payload) >> 8) & 0x0F), len(payload) & 0xFF]) + payload[:6]
            frames.append(ff_data)
            payload = payload[6:]
            
            # Consecutive frames
            sn = 1
            while payload:
                cf_data = bytes([0x20 | (sn & 0x0F)]) + payload[:7]
                frames.append(cf_data)
                payload = payload[7:]
                sn = (sn + 1) % 16
            
            for i, frame in enumerate(frames):
                self.send_message(tx_id, frame)
                if i == 0:
                    print(f"ISO-TP FF: {tx_id:03X} -> {len(data)} bytes total")
                    # Wait for flow control (simplified)
                    time.sleep(0.01)
                else:
                    print(f"ISO-TP CF: {tx_id:03X} [{i}]")
                    time.sleep(0.001)
    
    def close(self):
        self.running = False
        if self.log_file:
            self.log_file.close()
        if self.bus:
            self.bus.shutdown()

def signal_handler(sig, frame, can_interface):
    can_interface.close()
    sys.exit(0)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print("""
▄████▄   ▄▄▄       ███▄    █ ▄▄▄█████▓ ▒█████   ▒█████   ██▓      ██████ 
▒██▀ ▀█  ▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    ▒██    ▒ 
▒▓█    ▄ ▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    ░ ▓██▄   
▒▓▓▄ ▄██▒░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░      ▒   ██▒
▒ ▓███▀ ░ ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒▒██████▒▒
░ ░▒ ▒  ░ ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░▒ ▒▓▒ ▒ ░
░  ▒     ▒   ▒▒ ░░ ░░   ░ ▒░    ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░░ ░▒  ░ ░
░          ░   ▒      ░   ░ ░   ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░   ░  ░  ░  
░ ░            ░  ░         ░              ░ ░      ░ ░      ░  ░      ░  
░                                                                          

        🚗💨 macOS MeatPi CAN Interface Tool - for MeatPi OllieV2 🚗💨
""")
        print("=" * 80)
        print()
        print("USAGE:")
        print("  cantools.py <command> [options]")
        print()
        print("COMMANDS:")
        print("  connect <device>                    Test connection to CAN device")
        print("  send <device> <id> <data>           Send a CAN message")
        print("  listen <device>                     Listen for CAN messages")
        print("  replay <device> <file>              Replay logged CAN session")
        print("  generate <device> <id> <data>       Generate repeated CAN traffic")
        print("  isotp <device> <tx_id> <rx_id> <data>  Send ISO-TP diagnostic message")
        print("  sniffer <device>                    Real-time CAN bus monitor")
        print()
        print("SEND OPTIONS:")
        print("  --extended                          Use extended 29-bit CAN ID")
        print("  --rtr                              Send remote transmission request")
        print()
        print("LISTEN OPTIONS:")
        print("  --filter <id>                      Filter by CAN ID (hex)")
        print("  --filter <id:mask>                 Filter with ID and mask")
        print("  --log <file>                       Log messages to file")
        print("  --csv                              Use CSV format for logging")
        print("  --stats                            Show real-time statistics")
        print()
        print("REPLAY OPTIONS:")
        print("  --speed <multiplier>               Playback speed (default: 1.0)")
        print("  --loop                             Loop playback continuously")
        print()
        print("GENERATE OPTIONS:")
        print("  --interval <seconds>               Time between messages (default: 0.1)")
        print("  --count <number>                   Number of messages (default: infinite)")
        print()
        print("EXAMPLES:")
        print("  cantools.py connect /dev/cu.wchusbserial01234567891")
        print("  cantools.py send /dev/cu.device 0x123 DEADBEEF")
        print("  cantools.py send /dev/cu.device 0x1FFFFFFF CAFE --extended")
        print("  cantools.py listen /dev/cu.device --filter 0x700:0x7F0 --stats")
        print("  cantools.py listen /dev/cu.device --log session.csv --csv")
        print("  cantools.py generate /dev/cu.device 0x123 ABCD --interval 0.05 --count 100")
        print("  cantools.py replay /dev/cu.device session.csv --speed 2.0 --loop")
        print("  cantools.py isotp /dev/cu.device 0x7E0 0x7E8 1001")
        print("  cantools.py sniffer /dev/cu.device")
        print()
        print("DEVICE DISCOVERY:")
        print("  ls /dev/cu.*                       List all USB serial devices")
        print("  ls /dev/cu.*meatpi*                Find MEATPI devices specifically")
        print()
        return    
    command = sys.argv[1]
    device = sys.argv[2] if len(sys.argv) > 2 else None
    
    can_interface = CANInterface(device)
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, can_interface))
    
    if command == "connect":
        if can_interface.connect():
            print("Connected successfully")
        
    elif command == "send":
        can_id = int(sys.argv[3], 16)
        data = sys.argv[4]
        extended = "--extended" in sys.argv
        rtr = "--rtr" in sys.argv
        
        if can_interface.connect():
            can_interface.send_message(can_id, data, extended, rtr)
            
    elif command == "listen":
        log_file = None
        log_format = 'candump'
        show_stats = "--stats" in sys.argv
        
        if "--log" in sys.argv:
            log_idx = sys.argv.index("--log")
            log_file = sys.argv[log_idx + 1]
            log_format = 'csv' if "--csv" in sys.argv else 'candump'
            
        if "--filter" in sys.argv:
            filter_idx = sys.argv.index("--filter")
            filter_spec = sys.argv[filter_idx + 1]
            if ':' in filter_spec:
                can_id, mask = filter_spec.split(':')
                can_interface.add_filter(int(can_id, 16), int(mask, 16))
            else:
                can_interface.add_filter(int(filter_spec, 16))
        
        if can_interface.connect():
            if log_file:
                can_interface.start_logging(log_file, log_format)
            can_interface.listen(show_stats, log_format)
            
    elif command == "replay":
        filename = sys.argv[3]
        speed = 1.0
        loop = "--loop" in sys.argv
        
        if "--speed" in sys.argv:
            speed_idx = sys.argv.index("--speed")
            speed = float(sys.argv[speed_idx + 1])
        
        if can_interface.connect():
            can_interface.running = True
            can_interface.replay(filename, speed, loop)
            
    elif command == "generate":
        can_id = int(sys.argv[3], 16)
        data = sys.argv[4]
        interval = 0.1
        count = None
        
        if "--interval" in sys.argv:
            interval_idx = sys.argv.index("--interval")
            interval = float(sys.argv[interval_idx + 1])
            
        if "--count" in sys.argv:
            count_idx = sys.argv.index("--count")
            count = int(sys.argv[count_idx + 1])
        
        if can_interface.connect():
            can_interface.running = True
            can_interface.generate_traffic(can_id, data, interval, count)
            
    elif command == "isotp":
        tx_id = int(sys.argv[3], 16)
        rx_id = int(sys.argv[4], 16)
        data = bytes.fromhex(sys.argv[5])
        
        if can_interface.connect():
            can_interface.isotp_send(tx_id, rx_id, data)
            
    elif command == "sniffer":
        if can_interface.connect():
            can_interface.running = True
            # Top-like CAN sniffer
            import os
            
            try:
                while can_interface.running:
                    os.system('clear')
                    print("CAN Bus Activity Monitor")
                    print("=" * 50)
                    can_interface.print_stats()
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    
    can_interface.close()

if __name__ == "__main__":
    main()
    