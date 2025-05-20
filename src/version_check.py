#!/usr/bin/env python3
# src/version_check.py

import json, logging, os, requests

# 로컬 경로 (UTF-8 BOM 대응)
LOCAL_VERSION_PATH = os.path.join(os.path.dirname(__file__), '..', 'version.json')
# 반드시 Raw JSON URL 사용 (master 브랜치)
REMOTE_VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "ShovelMaker/LEB/"
    "master/version.json"
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_local_version() -> str:
    try:
        with open(LOCAL_VERSION_PATH, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data.get('version', '')
    except Exception as e:
        logging.error(f"로컬 버전 읽기 실패: {e}")
        return ''

def get_remote_version() -> str:
    try:
        r = requests.get(REMOTE_VERSION_URL, timeout=5)
        r.raise_for_status()
        text = r.content.decode('utf-8-sig')
        data = json.loads(text)
        return data.get('version', '')
    except Exception as e:
        logging.error(f"원격 버전 조회 실패: {e}")
        return ''

def check_for_update() -> (bool, str, str):
    local = get_local_version()
    remote = get_remote_version()
    if not local or not remote:
        return False, local, remote
    return (remote != local), local, remote
