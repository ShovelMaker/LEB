import os
import sqlite3
import subprocess
import json
import pytest

# 프로젝트 최상위 경로
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, 'scripts', 'update_resources.py')
DB_PATH = os.path.join(BASE_DIR, 'resources', 'resources.db')

@pytest.fixture(scope='module', autouse=True)
def run_update_script():
    # 기존 DB 제거
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # 스크립트 실행
    result = subprocess.run(
        ['python', SCRIPT_PATH],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
    assert os.path.exists(DB_PATH), "resources.db가 생성되지 않았습니다"
    return DB_PATH

def test_table_exists(run_update_script):
    conn = sqlite3.connect(run_update_script)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='endpoints';"
    )
    assert cursor.fetchone() is not None, "'endpoints' 테이블이 존재하지 않습니다"
    conn.close()

def test_endpoints_not_empty(run_update_script):
    conn = sqlite3.connect(run_update_script)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM endpoints;')
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0, f"endpoints 테이블이 비어있습니다 (count={count})"

@pytest.mark.parametrize('prefix', ['maxroll/items/'])
def test_sample_endpoint_json(run_update_script, prefix):
    conn = sqlite3.connect(run_update_script)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT data FROM endpoints WHERE endpoint LIKE ? LIMIT 1',
        (f'{prefix}%',)
    )
    row = cursor.fetchone()
    conn.close()
    assert row is not None, f"'{prefix}'로 시작하는 엔드포인트가 없습니다"
    # JSON 파싱 확인
    try:
        data = json.loads(row[0])
    except json.JSONDecodeError:
        pytest.fail('data 필드가 유효한 JSON이 아닙니다')
    assert isinstance(data, list), f"data는 리스트여야 합니다 (현재 {type(data)})"
