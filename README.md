# Custom STT Service for Home Assistant (renewed)

This integration provides a custom Speech-to-Text service for Home Assistant that converts audio to text using a specified API endpoint.

## Features

- WAV to MP3 conversion
- MAC address tracking
- Timestamp recording
- Secure API key management
- Korean language support

## Installation

### HACS Installation
1. Add this repository to HACS as a custom repository:
   - URL: `https://github.com/bluewhalekr/ha-stt-custom-integration`
   - Category: Integration
2. Click Install
3. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/custom_stt_renew_rs` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

Add to your `configuration.yaml`:

```yaml
custom_stt_renew_rs:
  language: ko-KR
  api_key: !secret custom_stt_renew_rs_api_key

stt:
  platform: custom_stt_renew_rs
```

Add to your `secrets.yaml`:
```yaml
custom_stt_renew_rs_api_key: "your-api-key-here"
```

## Requirements

- Home Assistant 2024.1.0 or newer
- FFmpeg
- Python packages: pydub, netifaces

## System Dependencies

Install required system packages:
```bash
pip3 install pydub netifaces
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Usage

This integration will register itself as an STT provider in Home Assistant. You can use it with any service that supports Home Assistant's STT interface.

## Support

- Report issues on GitHub
- Submit feature requests through the issue tracker

## License

This project is licensed under the MIT License - see the LICENSE file for details.