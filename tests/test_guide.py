import os
import pytest
import subprocess
import sys

# 프로젝트 루트 및 스크립트 경로
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
GUIDE_SCRIPT = os.path.join(BASE_DIR, 'src', 'guide.py')
OUTPUT_PATH = os.path.join(BASE_DIR, 'build_guide.html')

@pytest.fixture(autouse=True)
def cleanup_file():
    # 테스트 전후에 기존 출력 파일 제거
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
    yield
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)


def test_generate_guide_returns_path_and_creates_file():
    # guide.generate_guide 함수를 직접 임포트하여 호출
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    from guide import generate_guide

    path = generate_guide(output_path=OUTPUT_PATH)
    assert path == OUTPUT_PATH, f"생성된 파일 경로가 올바르지 않습니다: {path}"
    assert os.path.isfile(OUTPUT_PATH), "출력 파일이 생성되지 않았습니다"


def test_generate_guide_default_path(tmp_path, monkeypatch):
    # 인자 없이 호출 시 기본 경로 생성 확인
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    from guide import generate_guide

    # 작업 디렉토리 임시로 변경
    monkeypatch.chdir(tmp_path)
    path = generate_guide()
    default_file = tmp_path / 'build_guide.html'
    assert path == str(default_file), f"기본 생성 파일 경로가 잘못되었습니다: {path}"
    assert default_file.exists(), "기본 경로에 파일이 생성되지 않았습니다"
