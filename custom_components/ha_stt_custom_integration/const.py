"""
custom_components/remote_stt/const.py
상수 정의 업데이트
"""

DOMAIN = "remote_stt"
NAME = "Remote STT"

CONF_API_KEY = "api_key"
SERVER_URL = "https://rs-audio-router.azurewebsites.net/api/v1/audio-routing"

# 번역을 위한 문자열
STEP_USER_TITLE = "STT 서버 설정"
STEP_USER_DESCRIPTION = "STT 서버 연결을 위한 설정을 입력하세요."
ERROR_INVALID_AUTH = "인증 키가 올바르지 않습니다."
