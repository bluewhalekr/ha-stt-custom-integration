# Voice Processor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant 음성 어시스턴트를 위한 STT(Speech-to-Text) 제공자입니다.

## 기능
- 음성을 텍스트로 변환
- Home Assistant API 호출 실행
- 한국어 지원

## 설치 방법

### HACS를 통한 설치
1. HACS 실행
2. "Integrations" 메뉴로 이동
3. 우측 상단의 메뉴(⋮)를 클릭하고 "Custom repositories" 선택
4. Repository URL 입력: `https://github.com/bluewhalekr/ha-stt-custom-integration`
5. Category에서 "Integration" 선택
6. "ADD" 클릭
7. "Voice Processor" 설치
8. Home Assistant 재시작

## 설정

### 음성 어시스턴트 파이프라인 설정
1. 설정 > 음성 어시스턴트로 이동
2. 새 파이프라인 생성
3. STT 엔진으로 "Voice Processor STT" 선택
4. 설정 저장

## 지원
- 이슈 리포트: [GitHub Issues](https://github.com/bluewhalekr/ha-stt-custom-integration/issues)

"""info.md"""
# Voice Processor

Home Assistant 음성 어시스턴트를 위한 STT(Speech-to-Text) 제공자입니다.

## 특징
- 음성을 텍스트로 변환
- Home Assistant API 호출 실행
- 한국어 지원

## 설정
1. 설정 > 음성 어시스턴트로 이동
2. 새 파이프라인 생성
3. STT 엔진으로 "Voice Processor STT" 선택
4. 설정 저장