import paho.mqtt.client as mqtt
import ssl
import sys
import json
import base64
import binascii
from datetime import datetime

# MQTT Configuration
MQTT_CONFIG = {
    "MQTT_BROKER": "************.emqxsl.com",
    "MQTT_PORT": ****,
    "MQTT_TOPIC": "**********",
    "MQTT_TX_COMMAND_TOPIC": "********",
    "MQTT_USERNAME": "*******",
    "MQTT_PASSWORD": "*********"
}

class MQTTReader:
    def __init__(self):
        # Handle both old and new paho-mqtt versions
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            self.client = mqtt.Client()
        
        self.client.username_pw_set(MQTT_CONFIG["MQTT_USERNAME"], MQTT_CONFIG["MQTT_PASSWORD"])
        
        # Set TLS/SSL
        self.client.tls_set(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None
        )
        self.client.tls_insecure_set(False)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        self.data_count = 0
        self.total_bytes = 0
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✅ Connected to MQTT Broker: {MQTT_CONFIG['MQTT_BROKER']}")
            print(f"📡 Subscribing to topic: {MQTT_CONFIG['MQTT_TOPIC']}")
            
            # Subscribe to data topic
            client.subscribe(MQTT_CONFIG["MQTT_TOPIC"], qos=1)
            
            # Optional: Subscribe to command topic too
            client.subscribe(MQTT_CONFIG["MQTT_TX_COMMAND_TOPIC"], qos=1)
            print(f"📡 Also listening to: {MQTT_CONFIG['MQTT_TX_COMMAND_TOPIC']}")
        else:
            print(f"❌ Connection failed with code {rc}")
            sys.exit(1)
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        if rc != 0:
            print(f"⚠️ Unexpected disconnection: {rc}")
        else:
            print("✅ Disconnected from MQTT Broker")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        self.data_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        print(f"\n[{timestamp}] 📦 Message #{self.data_count}")
        print(f"  Topic: {msg.topic}")
        print(f"  Raw Payload Size: {len(msg.payload)} bytes")
        
        try:
            # Try to parse as JSON
            payload_json = json.loads(msg.payload.decode('utf-8'))
            
            print(f"  ✅ JSON Format Detected")
            print(f"  T (Type): {payload_json.get('T')}")
            print(f"  S (Sequence): {payload_json.get('S')}")
            
            d = payload_json.get('D', {})
            print(f"  D (Data):")
            print(f"    s_q: {d.get('s_q')}")
            print(f"    nwt (Total Chunks): {d.get('nwt')}")
            print(f"    fn (Filename): {d.get('fn')}")
            print(f"    fs (File Size): {d.get('fs'):,} bytes" if d.get('fs') else "    fs: N/A")
            print(f"    cn (Chunk Number): {d.get('cn')}")
            print(f"    cs (Chunk Size): {d.get('cs')} bytes")
            print(f"    crc (CRC32): {d.get('crc')}")
            
            # Decode base64 data
            if 'data' in d:
                try:
                    binary_data = base64.b64decode(d['data'])
                    print(f"    data: {len(binary_data)} bytes (base64 decoded)")
                    
                    # Verify CRC
                    actual_crc = binascii.crc32(binary_data) & 0xffffffff
                    expected_crc = d.get('crc', '')
                    crc_match = f"{actual_crc:08x}".lower() == expected_crc.lower()
                    crc_status = "✅ VALID" if crc_match else "❌ MISMATCH"
                    print(f"    CRC Verification: {crc_status} (Expected: {expected_crc}, Got: {actual_crc:08x})")
                    
                    # Update total bytes
                    self.total_bytes += len(binary_data)
                    print(f"  Total Received: {self.total_bytes:,} bytes")
                    
                    # Save to file
                    self.save_to_file(binary_data)
                except Exception as e:
                    print(f"    ❌ Error decoding base64: {e}")
        
        except json.JSONDecodeError:
            # Fallback to raw binary
            print(f"  ℹ️ Binary Format (not JSON)")
            payload_size = len(msg.payload)
            self.total_bytes += payload_size
            print(f"  Payload Size: {payload_size} bytes")
            print(f"  Total Received: {self.total_bytes:,} bytes")
            print(f"  Hex Data: {msg.payload[:50].hex()}")
            self.save_to_file(msg.payload)
    
    def save_to_file(self, data):
        """Save received data to file"""
        try:
            with open("received_data.bin", "ab") as f:
                f.write(data)
        except Exception as e:
            print(f"  ⚠️ Error saving to file: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print("🔗 Connecting to MQTT Broker...")
            self.client.connect(
                MQTT_CONFIG["MQTT_BROKER"],
                MQTT_CONFIG["MQTT_PORT"],
                keepalive=60
            )
            self.client.loop_forever()
        except Exception as e:
            print(f"❌ Connection error: {e}")
            sys.exit(1)

def main():
    print("=" * 60)
    print("🚀 MQTT Data Reader - BIN File Receiver")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Broker: {MQTT_CONFIG['MQTT_BROKER']}:{MQTT_CONFIG['MQTT_PORT']}")
    print(f"  Username: {MQTT_CONFIG['MQTT_USERNAME']}")
    print(f"  Data Topic: {MQTT_CONFIG['MQTT_TOPIC']}")
    print(f"  Command Topic: {MQTT_CONFIG['MQTT_TX_COMMAND_TOPIC']}")
    print(f"\n⏳ Waiting for incoming data...")
    print(f"📁 Data will be saved to: received_data.bin")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    reader = MQTTReader()
    
    try:
        reader.connect()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping MQTT Reader...")
        reader.client.disconnect()
        print(f"\n📊 Session Summary:")
        print(f"  Total Messages: {reader.data_count}")
        print(f"  Total Data Received: {reader.total_bytes:,} bytes")
        print("✅ Done!")

if __name__ == "__main__":
    main()

