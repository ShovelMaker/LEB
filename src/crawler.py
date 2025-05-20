#!/usr/bin/env python3
"""
src/crawler.py
Crawler module: handles data refresh for LEB.
"""
import os
import sys
import subprocess
import logging

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 스크립트 위치 설정 (프로젝트 루트/scripts/update_resources.py)
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, 'scripts', 'update_resources.py')


def refresh_all():
    """
    Run the update_resources script to rebuild resources.db.
    Returns True on success, False on failure.
    """
    logging.info('Starting full refresh...')
    if not os.path.isfile(UPDATE_SCRIPT):
        logging.error(f'Update script not found: {UPDATE_SCRIPT}')
        return False

    try:
        # subprocess.run with check=True raises CalledProcessError on non-zero exit
        result = subprocess.run(
            [sys.executable, UPDATE_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info('Update script output:\n%s', result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error('Update script failed with error:\n%s', e.stderr)
        return False

    # TODO: Add more data sources (mobaly, poe2, etc.) here

    logging.info('Full refresh completed successfully.')
    return True


if __name__ == '__main__':
    success = refresh_all()
    sys.exit(0 if success else 1)
