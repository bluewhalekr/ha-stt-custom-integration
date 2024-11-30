"""
Custom Speech-to-Text Integration for Home Assistant.
"""

import aiohttp
import logging
import datetime
import netifaces
from homeassistant.core import HomeAssistant
from homeassistant.components import stt
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from pydub import AudioSegment
import io
import json

_LOGGER = logging.getLogger(__name__)

DOMAIN = "custom_stt_renew_rs"
CONF_LANGUAGE = "language"
CONF_API_KEY = "api_key"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_LANGUAGE, default="ko-KR"): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def convert_wav_to_mp3(wav_data: bytes) -> bytes:
    """Convert WAV audio data to MP3 format."""
    try:
        audio = AudioSegment.from_wav(io.BytesIO(wav_data))
        mp3_buffer = io.BytesIO()
        audio.export(mp3_buffer, format="mp3", codec="libmp3lame")
        return mp3_buffer.getvalue()
    except Exception as e:
        _LOGGER.error(f"Error converting WAV to MP3: {str(e)}")
        raise


def get_first_ipv4_interface_mac():
    """Get MAC address of the first interface with IPv4."""
    try:
        for interface in netifaces.interfaces():
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:  # Has IPv4
                if netifaces.AF_LINK in addresses:  # Has MAC address
                    return addresses[netifaces.AF_LINK][0]["addr"]
    except Exception as e:
        _LOGGER.error(f"Error getting MAC address: {str(e)}")
    return None


async def async_setup(hass: HomeAssistant, config):
    """Set up the STT platform."""
    if DOMAIN not in config:
        return True

    conf = config.get(DOMAIN)
    language = conf.get(CONF_LANGUAGE)
    api_key = conf.get(CONF_API_KEY)

    hass.data[DOMAIN] = {"language": language, "api_key": api_key}

    hass.async_create_task(
        stt.async_setup_platform(
            hass, {"platform": DOMAIN, "language": language, "api_key": api_key}, async_setup_platform
        )
    )

    return True


async def async_setup_platform(hass, config, async_add_engine):
    """Set up STT engine."""
    language = config.get(CONF_LANGUAGE)
    api_key = config.get("api_key")
    engine = CustomSTTProvider(language, api_key)
    async_add_engine("custom_stt_renew_rs", engine)


class CustomSTTProvider(stt.Provider):
    """Custom STT provider."""

    def __init__(self, language, api_key):
        """Initialize the provider."""
        self.language = language
        self.api_key = api_key
        self.name = "Custom STT"

    @property
    def supported_languages(self):
        """Return a list of supported languages."""
        return ["ko-KR"]

    @property
    def supported_formats(self):
        """Return a list of supported formats."""
        return [stt.AudioFormats.WAV]

    async def async_process_audio_stream(self, metadata, stream):
        """Process audio stream and return transcribed text."""
        try:
            # Read WAV data
            wav_data = await stream.read()

            # Convert to MP3
            mp3_data = await convert_wav_to_mp3(wav_data)

            # Get metadata
            mac_address = get_first_ipv4_interface_mac()
            timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

            # Prepare metadata JSON
            json_data = {"text": "just test", "timestamp": str(timestamp), "macAddress": mac_address}

            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field("audio", mp3_data, filename="audio.mp3", content_type="audio/mpeg")

            form_data.add_field("data", json.dumps(json_data), content_type="application/json")

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://rs-audio-router.azurewebsites.net/api/v1/audio-routing",
                    headers={"x-functions-key": self.api_key},
                    data=form_data,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(f"API error: {response.status}, {error_text}")
                        raise stt.SpeechToTextError(f"API error: {response.status}")

                    result = await response.text()
                    return stt.SpeechResult(result, self.language)

        except Exception as err:
            _LOGGER.error(f"STT processing error: {str(err)}")
            raise stt.SpeechToTextError(f"STT processing error: {str(err)}")
