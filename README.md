# 📦 MQTT BIN File Streamer

A robust Streamlit application for uploading and receiving binary files over MQTT with JSON payload format, CRC32 integrity checking, and SSL/TLS encryption.

## Features

✅ **Sender (app.py)**
- Upload .bin files via Streamlit UI
- Send 250-byte chunks every 2 seconds
- JSON payload with headers (T, S, D)
- Base64-encoded binary data
- CRC32 checksum verification
- Real-time progress tracking
- SSL/TLS encrypted connection

✅ **Receiver (mqtt_reader.py)**
- Listen to MQTT topic for incoming data
- Parse JSON payloads automatically
- Verify CRC32 checksums
- Reconstruct original binary file
- Display transmission statistics
- Support for both JSON and raw binary formats

## JSON Payload Format

```json
{
  "T": 40,
  "S": <sequence_number>,
  "D": {
    "s_q": 18,
    "nwt": <total_chunks>,
    "fn": "<filename>",
    "fs": <file_size>,
    "cn": <chunk_number>,
    "cs": <chunk_size>,
    "crc": "<crc32_hex>",
    "data": "<base64_encoded_binary>"
  }
}
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone the repository**
```bash
[https://github.com/manoharreddyvoladri/mqtt-bin-streamer.git]
cd mqtt-bin-streamer
```

2. **Create virtual environment** (optional but recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the project root:
```bash
MQTT_BROKER= *****.emqxsl.com
MQTT_PORT=8883
MQTT_TOPIC=vehicle/bin_Data/data
MQTT_TX_COMMAND_TOPIC=vehicle/tx_cmd
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

Then update the code to load from environment:

**For app.py:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

MQTT_CONFIG = {
    "MQTT_BROKER": os.getenv("MQTT_BROKER", "******.emqxsl.com"),
    "MQTT_PORT": int(os.getenv("MQTT_PORT", 8883)),
    "MQTT_TOPIC": os.getenv("MQTT_TOPIC", "vehicle/bin_Data/data"),
    "MQTT_TX_COMMAND_TOPIC": os.getenv("MQTT_TX_COMMAND_TOPIC", "vehicle/tx_cmd"),
    "MQTT_USERNAME": os.getenv("MQTT_USERNAME", ""),
    "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD", "")
}
```

**For mqtt_reader.py:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

MQTT_CONFIG = {
    "MQTT_BROKER": os.getenv("MQTT_BROKER", "****.emqxsl.com"),
    "MQTT_PORT": int(os.getenv("MQTT_PORT", 8883)),
    "MQTT_TOPIC": os.getenv("MQTT_TOPIC", "vehicle/bin_Data/data"),
    "MQTT_TX_COMMAND_TOPIC": os.getenv("MQTT_TX_COMMAND_TOPIC", "vehicle/tx_cmd"),
    "MQTT_USERNAME": os.getenv("MQTT_USERNAME", ""),
    "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD", "")
}
```

### Option 2: Config File

Create a `config.json` file:
```json
{
  "MQTT_BROKER": "**********.emqxsl.com",
  "MQTT_PORT": PORT,
  "MQTT_TOPIC": "***",
  "MQTT_TX_COMMAND_TOPIC": "*****",
  "MQTT_USERNAME": "your_username",
  "MQTT_PASSWORD": "your_password"
}
```

Then in code:
```python
import json

with open('config.json') as f:
    MQTT_CONFIG = json.load(f)
```

### Option 3: Command Line Arguments

```bash
# For app.py
streamlit run app.py

# For mqtt_reader.py
python mqtt_reader.py 
```

## Usage

### Running the Sender (Uploader)

```bash
streamlit run app.py
```

1. Open http://localhost:8501 in your browser
2. Click "🔗 Connect" in the sidebar
3. Upload a .bin file
4. Click "🚀 Send File"
5. Monitor real-time progress

### Running the Receiver

```bash
python mqtt_reader.py
```

The receiver will:
- Connect to MQTT broker
- Listen on configured topic
- Display incoming chunks with metadata
- Save reconstructed file to `received_data.bin`
- Show CRC32 verification status
- Press Ctrl+C to stop

## File Structure

```
mqtt-bin-streamer/
├── app.py                  # Streamlit sender application
├── mqtt_reader.py          # Receiver script
├── requirements.txt        # Python dependencies
├── config.json            # Configuration file (optional)
├── .env                   # Environment variables (optional)
├── .gitignore             # Git ignore file
└── README.md              # This file
```

## Example .gitignore

```
# Environment variables
.env
.env.local

# Config files with credentials
config.json

# Received data
received_data.bin

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Troubleshooting

### Connection Errors
- Verify MQTT broker address and port
- Check username and password
- Ensure SSL/TLS certificates are valid
- Check firewall settings

### CRC32 Mismatch
- Indicates data corruption during transmission
- Check network connection quality
- Retry transmission

### Base64 Decoding Errors
- Ensure JSON payload is complete
- Check if binary data is properly encoded

## Author

Created for MQTT-based binary file transfer with integrity checking and real-time monitoring.



