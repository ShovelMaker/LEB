#!/usr/bin/env python3
import os
import sqlite3
import subprocess
import pytest

# 이 테스트는 scripts/update_resources.py 스크립트가 정상 작동하여
# resources/resources.db를 생성·업데이트하는지 검증합니다.
# 프로젝트 루트 기준으로 테스트가 실행되어야 합니다.

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, 'scripts', 'update_resources.py')
DB_PATH = os.path.join(BASE_DIR, 'resources', 'resources.db')

@pytest.fixture(autouse=True)
def clean_db_before_and_after():
    # 테스트 전후 resources.db 삭제
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def test_update_resources_creates_db_and_table():
    # 스크립트 실행
    result = subprocess.run(
        ['python', SCRIPT_PATH],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Script error: {result.stderr}"
    # DB 파일 생성 확인
    assert os.path.isfile(DB_PATH), "resources.db가 생성되지 않았습니다"

    # 테이블 확인
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='endpoints';"
    )
    table_count = cur.fetchone()[0]
    conn.close()
    assert table_count == 1, "endpoints 테이블이 존재하지 않습니다"


def test_endpoints_table_not_empty():
    # resources.db가 존재한다고 가정하고 다시 생성
    subprocess.run(['python', SCRIPT_PATH], capture_output=True, text=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM endpoints;')
    row_count = cur.fetchone()[0]
    conn.close()
    assert row_count > 0, f"endpoints 테이블이 비어 있습니다 (count={row_count})"


@pytest.mark.parametrize("prefix", ["maxroll/items/"])
def test_sample_endpoint_data(prefix):
    # DB가 준비된 상태에서 데이터 형식 검증
    subprocess.run(['python', SCRIPT_PATH], capture_output=True, text=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'SELECT data FROM endpoints WHERE endpoint LIKE ? LIMIT 1',
        (f'{prefix}%',)
    )
    result = cur.fetchone()
    conn.close()

    assert result is not None, f"'{prefix}'로 시작하는 엔드포인트가 없습니다"
    import json
    try:
        items = json.loads(result[0])
    except json.JSONDecodeError:
        pytest.fail("data 필드가 올바른 JSON이 아닙니다")
    assert isinstance(items, list), f"data는 리스트여야 합니다 (현재 {type(items)})"
