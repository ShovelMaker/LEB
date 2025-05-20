#!/usr/bin/env python3
"""
Build and update resources.db from Maxroll data.json
Usage: python update_resources.py
"""
import os
import json
import sqlite3
import requests
import logging
import sys

# ─── 설정 영역 ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "resources", "resources.db")
DATA_URL = "https://assets-ng.maxroll.gg/leplanner/game/data.json?1ee4237b"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}
# ────────────────────────────────────────────────────────

def create_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS endpoints (
                endpoint TEXT PRIMARY KEY,
                data     TEXT NOT NULL
            )
            """
        )
        conn.commit()
        return conn
    except sqlite3.Error as e:
        logging.critical(f"DB 생성/연결 실패: {e}")
        sys.exit(1)


def build_db():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    try:
        logging.info(f"Fetching JSON: {DATA_URL}")
        resp = requests.get(DATA_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logging.error(f"HTTP 요청 실패: {e}")
        sys.exit(1)

    conn = create_db()
    cursor = conn.cursor()

    # 데이터 구조에 따른 카테고리 처리
    if isinstance(data.get("categories"), list) and isinstance(data.get("items"), dict):
        categories = [cat.get("key") for cat in data["categories"] if isinstance(cat, dict) and "key" in cat]
        get_items = lambda key: data["items"].get(key, [])
    elif isinstance(data.get("items"), dict):
        categories = list(data["items"].keys())
        get_items = lambda key: data["items"].get(key, [])
    else:
        # fallback: 최상위 리스트 타입 키를 카테고리로
        categories = [k for k, v in data.items() if isinstance(v, list)]
        get_items = lambda key: data.get(key, [])
        logging.warning(f"Fallback category list: {categories}")
        if not categories:
            logging.error("데이터 구조를 파악할 수 없어 종료합니다.")
            sys.exit(1)

    # 각 카테고리별 DB 저장
    for key in categories:
        items_list = get_items(key) or []
        ep = f"maxroll/items/{key}"
        try:
            cursor.execute(
                "REPLACE INTO endpoints (endpoint, data) VALUES (?, ?)",
                (ep, json.dumps(items_list, ensure_ascii=False))
            )
            conn.commit()
            logging.info(f"Saved {ep} ({len(items_list)} items)")
        except sqlite3.Error as e:
            logging.error(f"DB 저장 실패 {ep}: {e}")
            conn.rollback()

    conn.close()
    logging.info("▶ resources.db build complete.")

if __name__ == "__main__":
    build_db()
