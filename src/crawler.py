# D:\LEB\src\crawler.py

import os
import sys
import subprocess
import logging

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s (crawler): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPDATE_SCRIPT_NAME = 'update_resources.py'
UPDATE_SCRIPT_PATH = os.path.join(BASE_DIR, 'scripts', UPDATE_SCRIPT_NAME)

def refresh_all():
    """
    scripts/update_resources.py 스크립트를 실행하여 resources.db를 업데이트합니다.
    Returns:
        dict: 작업 성공 여부와 함께 표준 출력 또는 오류 메시지를 포함하는 딕셔너리.
    """
    logger.info(f"'{UPDATE_SCRIPT_NAME}' 스크립트를 사용한 전체 데이터 새로고침을 시작합니다...")
    
    if not os.path.isfile(UPDATE_SCRIPT_PATH):
        error_message = f"오류: 업데이트 스크립트를 찾을 수 없습니다 - {UPDATE_SCRIPT_PATH}"
        logger.error(error_message)
        return {'success': False, 'output': error_message}

    try:
        process = subprocess.run(
            [sys.executable, UPDATE_SCRIPT_PATH],
            capture_output=True,
            check=True, # 반환 코드가 0이 아니면 CalledProcessError 발생
            cwd=os.path.join(BASE_DIR, 'scripts') 
        )
        
        # 바이트 출력을 'utf-8'로 디코딩 (오류 발생 시 대체 문자로)
        stdout_str = process.stdout.decode('utf-8', errors='replace').strip()
        stderr_str = process.stderr.decode('utf-8', errors='replace').strip() # 성공 시에도 stderr 확인 가능

        combined_output_parts = []
        if stdout_str:
            combined_output_parts.append(f"--- 표준 출력 (STDOUT) ---\n{stdout_str}")
        if stderr_str: # 성공 시에도 stderr에 로그가 남을 수 있음 (특히 로깅 라이브러리 사용 시)
            combined_output_parts.append(f"--- 표준 오류 (STDERR) ---\n{stderr_str}")
        
        final_output = "\n\n".join(combined_output_parts).strip()
        
        if not final_output:
             final_output = f"'{UPDATE_SCRIPT_NAME}' 스크립트가 성공적으로 실행되었으나, 별도의 출력 메시지가 없습니다."

        logger.info(f"'{UPDATE_SCRIPT_NAME}' 스크립트가 성공적으로 실행되었습니다.")
        return {'success': True, 'output': final_output}

    except subprocess.CalledProcessError as e:
        stdout_str = e.stdout.decode('utf-8', errors='replace').strip() if e.stdout else "내용 없음"
        stderr_str = e.stderr.decode('utf-8', errors='replace').strip() if e.stderr else "내용 없음"
        
        error_details = (
            f"'{UPDATE_SCRIPT_NAME}' 스크립트 실행 중 오류가 발생했습니다 (종료 코드: {e.returncode}).\n"
            f"--- 표준 출력 (STDOUT) ---\n{stdout_str}\n"
            f"--- 표준 오류 (STDERR) ---\n{stderr_str}"
        )
        logger.error(error_details)
        return {'success': False, 'output': error_details}
    
    except FileNotFoundError:
        error_message = f"오류: 파이썬 실행 파일 또는 '{UPDATE_SCRIPT_NAME}' 스크립트 경로를 찾을 수 없습니다."
        logger.error(error_message)
        return {'success': False, 'output': error_message}
        
    except Exception as e:
        error_message = f"'{UPDATE_SCRIPT_NAME}' 스크립트 실행 중 예상치 못한 오류 발생: {e}"
        logger.exception(error_message)
        return {'success': False, 'output': error_message}

if __name__ == '__main__':
    print(f"'{UPDATE_SCRIPT_NAME}' 스크립트 단독 실행 테스트...")
    result = refresh_all()
    print("\n--- 실행 결과 ---")
    print(f"성공 여부: {result['success']}")
    print(f"출력 내용:\n{result['output']}")
    sys.exit(0 if result['success'] else 1)
