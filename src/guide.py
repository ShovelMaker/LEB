#!/usr/bin/env python3
"""
src/guide.py
빌드 가이드를 생성하는 더미 모듈
"""
import logging
import os

def generate_guide(output_path=None):
    """
    직업·레벨·버전별 빌드 가이드를 생성합니다.
    - output_path: 저장할 파일 경로 (PDF/HTML 등)
    반환값: 생성된 파일 경로 또는 None
    """
    logging.info("가이드 생성 시작…")
    # TODO: GPT API 호출 및 템플릿 채우기
    if output_path is None:
        output_path = os.path.join(os.getcwd(), "build_guide.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("<h1>LEB Build Guide</h1><p>준비 중…</p>")
    logging.info(f"가이드 생성 완료: {output_path}")
    return output_path
