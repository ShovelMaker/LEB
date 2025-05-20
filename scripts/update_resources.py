#!/usr/bin/env python3
# scripts/update_resources.py

import json
import urllib.request
import urllib.error
import os
import sys

# → 반드시 GitHub 'Raw' URL을 가리켜야 합니다!
UPDATE_INFO_URL = "https://raw.githubusercontent.com/ShovelMaker/LEB/main/version.json"

def fetch_json(url):
    """
    주어진 URL에서 JSON을 가져와 파싱해서 반환합니다.
    HTTP 에러 발생 시 메시지를 출력하고 종료합니다.
    """
    try:
        with urllib.request.urlopen(url) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"✖ HTTP error fetching {url}: {e.code} {e.reason}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✖ JSON 파싱 오류 for {url}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✖ Error fetching {url}: {e}")
        sys.exit(1)

def main():
    local_path = "version.json"
    # 1) 로컬 version.json 읽기 (BOM 처리 위해 utf-8-sig 사용)
    if not os.path.isfile(local_path):
        print(f"✖ 로컬 버전 파일이 없습니다: {local_path}")
        sys.exit(1)

    try:
        with open(local_path, encoding="utf-8-sig") as f:
            local = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✖ 로컬 JSON 파싱 오류: {e}")
        sys.exit(1)

    print(f"Local version: {local.get('version', '<unknown>')}")

    # 2) 원격 version.json 읽기
    remote = fetch_json(UPDATE_INFO_URL)
    print(f"Remote version: {remote.get('version', '<unknown>')}")

    # 3) 버전 비교
    if local.get("version") == remote.get("version"):
        print("✔ 최신 버전입니다.")
    else:
        print("▶ 업데이트가 있습니다!")
        print(f"    로컬:  {local['version']}")
        print(f"    원격:  {remote['version']}")
        # TODO: 자동 업데이트 로직(예: git pull 또는 파일 다운로드) 추가 가능

if __name__ == "__main__":
    main()
