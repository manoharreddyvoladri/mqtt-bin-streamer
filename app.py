import streamlit as st
import paho.mqtt.client as mqtt
import time
import threading
from pathlib import Path
import ssl
import json
import base64
import binascii

# MQTT Configuration
MQTT_CONFIG = {
    "MQTT_BROKER": "**************.emqxsl.com",
    "MQTT_PORT": ****,
    "MQTT_TOPIC": "***********",
    "MQTT_TX_COMMAND_TOPIC": "********",
    "MQTT_USERNAME": "***",
    "MQTT_PASSWORD": "***"
}

CHUNK_SIZE = 250  # bytes
SEND_INTERVAL = 2  # seconds

def calculate_crc32(data):
    """Calculate CRC32 checksum of data"""
    return binascii.crc32(data) & 0xffffffff

def create_payload(chunk_data, chunk_num, total_chunks, filename, file_size):
    """
    Create JSON payload with headers and base64-encoded bin data
    Format:
    {
        "T": 40,
        "S": <sequence>,
        "D": {
            "s_q": 18,
            "nwt": <total_chunks>,
            "fn": <filename>,
            "fs": <file_size>,
            "cn": <chunk_num>,
            "cs": <chunk_size>,
            "crc": <crc32_checksum>,
            "data": <base64_encoded_binary>
        }
    }
    """
    crc_checksum = calculate_crc32(chunk_data)
    
    payload = {
        "T": 40,
        "S": chunk_num,
        "D": {
            "s_q": 18,
            "nwt": total_chunks,
            "fn": filename,
            "fs": file_size,
            "cn": chunk_num,
            "cs": len(chunk_data),
            "crc": f"{crc_checksum:08x}",
            "data": base64.b64encode(chunk_data).decode('utf-8')
        }
    }
    
    return json.dumps(payload)

class MQTTClient:
    def __init__(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_CONFIG["MQTT_USERNAME"], MQTT_CONFIG["MQTT_PASSWORD"])
        self.client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        self.client.tls_insecure_set(False)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            st.session_state.status_message = "✅ Connected to MQTT Broker"
        else:
            st.session_state.status_message = f"❌ Connection failed with code {rc}"
    
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            st.session_state.status_message = f"⚠️ Disconnected with code {rc}"
    
    def on_publish(self, client, userdata, mid):
        pass
    
    def connect(self):
        try:
            self.client.connect(MQTT_CONFIG["MQTT_BROKER"], MQTT_CONFIG["MQTT_PORT"], keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            st.session_state.status_message = f"❌ Connection error: {str(e)}"
            return False
    
    def publish(self, topic, payload):
        try:
            result = self.client.publish(topic, payload, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            st.session_state.status_message = f"❌ Publish error: {str(e)}"
            return False
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

def send_bin_file_chunks(file_bytes, filename, mqtt_client, progress_placeholder, status_placeholder):
    """Send BIN file in 250-byte chunks every 2 seconds with JSON payload"""
    total_chunks = (len(file_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
    file_size = len(file_bytes)
    
    for chunk_num in range(total_chunks):
        if not st.session_state.get("is_sending", False):
            break
        
        start_idx = chunk_num * CHUNK_SIZE
        end_idx = min(start_idx + CHUNK_SIZE, len(file_bytes))
        chunk = file_bytes[start_idx:end_idx]
        
        # Create JSON payload with headers
        payload_json = create_payload(chunk, chunk_num + 1, total_chunks, filename, file_size)
        
        # Publish chunk
        success = mqtt_client.publish(MQTT_CONFIG["MQTT_TOPIC"], payload_json)
        
        # Update progress
        progress = (chunk_num + 1) / total_chunks
        progress_placeholder.progress(progress)
        
        payload_size = len(payload_json.encode('utf-8'))
        crc = calculate_crc32(chunk)
        chunk_info = f"📤 Chunk {chunk_num + 1}/{total_chunks} | Size: {len(chunk)}B | CRC32: {crc:08x} | JSON: {payload_size}B"
        status_placeholder.info(chunk_info)
        
        # Wait 2 seconds before sending next chunk (except for last chunk)
        if chunk_num < total_chunks - 1:
            time.sleep(SEND_INTERVAL)
    
    status_placeholder.success(f"✅ Transmission complete! Sent {total_chunks} chunks")
    st.session_state.is_sending = False

# Streamlit App
st.set_page_config(page_title="BIN File MQTT Uploader", layout="wide")

st.title("📦 BIN File MQTT Uploader")

# Initialize session state
if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None
if "is_sending" not in st.session_state:
    st.session_state.is_sending = False
if "status_message" not in st.session_state:
    st.session_state.status_message = "Ready"

# Sidebar Configuration
with st.sidebar:
    st.header("MQTT Configuration")
    st.json(MQTT_CONFIG)
    
    # Connection Status
    status_col = st.columns([3, 1])
    with status_col[0]:
        st.text(f"Status: {st.session_state.status_message}")
    
    with status_col[1]:
        if st.session_state.mqtt_client is None or not st.session_state.mqtt_client.connected:
            if st.button("🔗 Connect", use_container_width=True):
                mqtt_client = MQTTClient()
                if mqtt_client.connect():
                    st.session_state.mqtt_client = mqtt_client
                    time.sleep(1)
                    st.rerun()
        else:
            if st.button("🔌 Disconnect", use_container_width=True):
                st.session_state.mqtt_client.disconnect()
                st.session_state.mqtt_client = None
                st.rerun()

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload BIN File")
    uploaded_file = st.file_uploader("Select a .bin file", type="bin")
    
    if uploaded_file is not None:
        st.success(f"✅ File selected: {uploaded_file.name}")
        st.info(f"📊 File size: {uploaded_file.size:,} bytes")
        st.info(f"📦 Will send in {(uploaded_file.size + CHUNK_SIZE - 1) // CHUNK_SIZE} chunks of {CHUNK_SIZE} bytes")
        st.info(f"⏱️ Interval: {SEND_INTERVAL} seconds between chunks")

with col2:
    st.subheader("📊 Transmission Stats")
    if uploaded_file is not None:
        total_size = uploaded_file.size
        num_chunks = (total_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        total_time = num_chunks * SEND_INTERVAL - SEND_INTERVAL  # Last chunk doesn't wait
        
        st.metric("Total Size", f"{total_size:,} bytes")
        st.metric("Number of Chunks", num_chunks)
        st.metric("Est. Time", f"{total_time}s")

# Send Button
st.divider()

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 Send File", use_container_width=True, disabled=not (st.session_state.mqtt_client and st.session_state.mqtt_client.connected)):
            if st.session_state.mqtt_client and st.session_state.mqtt_client.connected:
                st.session_state.is_sending = True
                
                # Create placeholders for progress and status
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                # Read file bytes
                file_bytes = uploaded_file.getvalue()
                
                # Send chunks with JSON payload
                send_bin_file_chunks(file_bytes, uploaded_file.name, st.session_state.mqtt_client, progress_placeholder, status_placeholder)
            else:
                st.error("❌ Not connected to MQTT broker. Please connect first.")
    
    with col2:
        if st.button("⏹️ Stop", use_container_width=True, disabled=not st.session_state.is_sending):
            st.session_state.is_sending = False
            st.warning("⏸️ Transmission stopped")

# Instructions
with st.expander("ℹ️ How it works"):
    st.markdown("""
    1. **Connect to MQTT**: Click the "Connect" button in the sidebar to establish connection
    2. **Upload BIN File**: Select a .bin file to upload
    3. **Review Details**: Check the file size and transmission stats
    4. **Send File**: Click "Send File" to start transmission
    5. **Monitor Progress**: Watch the progress bar and chunk information
    
    **Features:**
    - Sends 250 bytes every 2 seconds
    - JSON payload format with headers and binary data
    - Base64-encoded binary data
    - CRC32 checksum for integrity verification
    - SSL/TLS encrypted connection to MQTT broker
    - Real-time progress tracking
    
    **JSON Payload Format:**
    ```json
    {
      "T": 40,
      "S": <sequence_number>,
      "D": {
        "s_q": 18,
        "nwt": <total_chunks>,
        "fn": <filename>,
        "fs": <file_size>,
        "cn": <chunk_number>,
        "cs": <chunk_size>,
        "crc": <crc32_hex>,
        "data": <base64_encoded_binary>
      }
    }
    ```
    """)

st.divider()
st.caption("🔒 Secure MQTT Connection | BIN File Uploader v1.0")

