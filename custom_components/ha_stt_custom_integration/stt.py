"""Voice Assistant STT Provider for Home Assistant."""

import datetime
import io
import logging
import wave
from collections.abc import AsyncIterable
from typing import Any

import async_timeout
import netifaces
import requests
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    Provider,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)


class RemoteSTTProvider(Provider):
    """Remote STT provider for Voice Assistant."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the provider."""
        self.hass = hass
        self.api_key = entry.data[CONF_API_KEY]
        self.name = "Remote STT Provider"

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["ko-KR"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def convert_wav_to_mp3(self, wav_data: bytes) -> bytes:
        """Convert WAV audio data to MP3 format."""
        try:
            audio = AudioSegment.from_wav(io.BytesIO(wav_data))
            mp3_buffer = io.BytesIO()
            audio.export(mp3_buffer, format="mp3", codec="libmp3lame")
            return mp3_buffer.getvalue()
        except Exception as e:
            _LOGGER.error(f"Error converting WAV to MP3: {str(e)}")
            raise

    def get_first_ipv4_interface_mac(self):
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

    def is_detect_voice(
        self, audio_segment, thresh=-50, min_silence_len=500, silence_thresh=-70
    ):
        """Detects non-silent parts of the audio and returns True if silence is predominant."""
        if not isinstance(audio_segment, AudioSegment):
            _LOGGER.error(
                "Expected an instance of AudioSegment, got type of {}".format(
                    type(audio_segment)
                )
            )

        # 비침묵 구간 검출
        nonsilent_ranges = detect_nonsilent(
            audio_segment,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )

        _LOGGER.debug(nonsilent_ranges)

        # 감지된 무음이 아닌 구간 중 임계값 이상의 소리가 있는지 검사
        for start_i, end_i in nonsilent_ranges:
            segment = audio_segment[start_i:end_i]
            if segment.dBFS > thresh:
                return True

        return False

    async def async_send_audio_data(self, file_path, text):
        url = "https://rs-audio-router.azurewebsites.net/api/v1/audio-routing"
        mac_address = netifaces.ifaddresses("end0")[netifaces.AF_LINK][0]["addr"]
        timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        headers = {"x-functions-key": self.api_key}
        data = {"text": text, "timestamp": str(timestamp), "macAddress": mac_address}
        _LOGGER.debug(f"$$$ filename : {file_path},  datas: {data}")

        def job():
            with open(file_path, "rb") as file:
                files = {"audio": file}
                response = requests.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                return response.json()

        try:
            async with async_timeout.timeout(10):
                response = await self.hass.async_add_executor_job(job)
                _LOGGER.debug(f"$$$ Response : {response}")
                return response
        except Exception as e:
            # print(f"An error occurred: {e}")
            _LOGGER.error(f"An error occurred: {e}")
            return None

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process the audio stream and return the speech result."""
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        _LOGGER.debug(f"$$$ voice data size : {len(audio_data)}")
        if len(audio_data) <= 1000:
            _LOGGER.debug("No audio data received.")
            return SpeechResult("", SpeechResultState.ERROR)

        # Create an audio stream that complies with the API requirements
        wav_stream = io.BytesIO()
        with wave.open(wav_stream, "wb") as wf:
            wf.setnchannels(metadata.channel)
            wf.setsampwidth(metadata.bit_rate // 8)
            wf.setframerate(metadata.sample_rate)
            wf.writeframes(audio_data)

        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        mp3_path = f"/config/stt/stt_{current_time}.mp3"

        def job():
            # Convert WAV to MP3
            wav_stream.seek(0)  # 스트림의 위치를 처음으로 되돌림
            sound = AudioSegment.from_file(wav_stream, format="wav")

            is_voice = self.is_detect_voice(sound)
            _LOGGER.debug(f"$$$ is voice detect : {is_voice}")
            if not is_voice:
                return SpeechResult("", SpeechResultState.ERROR)

            sound.export(mp3_path, format="mp3")
            return mp3_path

        async with async_timeout.timeout(10):
            response = await self.hass.async_add_executor_job(job)
            if response:
                # await self.async_send_audio_data(mp3_path, response.text)
                self.hass.create_task(
                    self.async_send_audio_data(mp3_path, "transcribed text")
                )
                return SpeechResult(
                    "transcribed text",
                    SpeechResultState.SUCCESS,
                )
            return SpeechResult("", SpeechResultState.ERROR)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Remote STT from a config entry."""
    api_key = entry.data[CONF_API_KEY]

    # STT Provider 등록
    provider = RemoteSTTProvider(hass, api_key)
    hass.components.stt.async_register(DOMAIN, provider)
