# D:\LEB\tests\test_guide.py

import pytest
import os
import sys # BASE_DIR 정의 등에 필요할 수 있습니다.
from pathlib import Path # tmp_path 등 경로 관련 작업을 위해 추가

# ####################################################################
# # src.guide 모듈에서 generate_guide 함수를 임포트합니다.
# # pytest.ini의 pythonpath = . 설정 덕분에 이 방식이 가능해야 합니다.
# ####################################################################
try:
    from src.guide import generate_guide
except ImportError:
    # 만약 위 import가 실패하면, 이전 방식(sys.path 조작)을 임시로 사용할 수 있지만,
    # 근본적으로 pytest.ini 설정을 점검하는 것이 좋습니다.
    # 여기서는 pytest.ini가 올바르다는 가정 하에 진행합니다.
    # pytest 실행 시 이 부분이 실패하면 ModuleNotFoundError가 발생할 것입니다.
    # 지금은 NameError이므로, 아래처럼 임포트가 안된 것으로 간주합니다.
    generate_guide = None # 임시 할당 (테스트 실패 유도)
    print("경고: from src.guide import generate_guide 실패! NameError가 발생할 수 있습니다.")


# 이 파일(test_guide.py)의 위치를 기준으로 프로젝트 루트(BASE_DIR) 설정
# test_guide.py는 D:\LEB\tests\ 안에 있으므로, BASE_DIR은 두 단계 위입니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 테스트용 출력 파일을 저장할 임시 디렉토리 또는 특정 디렉토리
# pytest의 tmp_path fixture를 사용하는 것이 더 깔끔하지만, 우선은 경로를 정의해봅니다.
# generate_guide 함수는 이제 BASE_DIR/guides/ 경로에 파일을 생성하므로,
# 테스트에서는 해당 경로에 파일이 생성되었는지 확인해야 합니다.
# 또는 테스트용으로 다른 output_filename_base를 사용하고 tmp_path에 저장할 수도 있습니다.

# 테스트용 샘플 파라미터
SAMPLE_PARAMS_FOR_TEST = {
    'class': 'TestClass', 'mastery': 'TestMastery', 'level': 1, 'hardcore': False,
    'build_type': 'TestBuild', 'game_version': 'TestVersion'
}
SAMPLE_PARAMS_FOR_DEFAULT_TEST = {
    'class': 'DefaultClass', 'level': 1
}


def test_generate_guide_is_importable():
    """generate_guide 함수가 임포트되었는지 간단히 확인"""
    assert generate_guide is not None, "'generate_guide' 함수가 임포트되지 않았습니다."
    assert callable(generate_guide), "'generate_guide'는 호출 가능한 함수여야 합니다."

def test_generate_guide_returns_path_and_creates_file(tmp_path: Path):
    """
    generate_guide 함수가 파일 경로를 반환하고, 실제로 파일을 생성하는지 테스트합니다.
    pytest의 tmp_path fixture를 사용하여 임시 디렉토리에 파일을 생성하도록 유도합니다.
    """
    if not callable(generate_guide):
        pytest.skip("'generate_guide' 함수를 임포트할 수 없어 테스트를 건너뜁니다.")

    # generate_guide 함수는 BASE_DIR/guides/ 경로에 파일을 생성합니다.
    # 테스트에서는 임시 경로를 사용하도록 output_filename_base를 조작하거나,
    # monkeypatch를 사용해 BASE_DIR을 tmp_path로 변경할 수 있습니다.
    # 여기서는 함수가 반환하는 경로에 파일이 생성되는지만 확인합니다.
    
    # 파일 기본 이름을 지정합니다. 실제 파일명에는 파라미터가 포함될 수 있습니다.
    test_output_base = "test_guide_output_in_temp" 
    
    # monkeypatch를 사용하여 BASE_DIR을 tmp_path로 변경하여 guides 폴더가 tmp_path 아래에 생성되도록 함
    # (또는 generate_guide 함수가 출력 디렉토리를 인자로 받도록 수정하는 것도 방법)
    # 현재 generate_guide는 BASE_DIR을 내부적으로 사용하므로, 
    # 여기서는 output_filename_base에 tmp_path를 포함시키는 트릭을 사용하거나,
    # generate_guide가 절대 경로를 받을 수 있도록 수정해야 합니다.
    # 지금은 generate_guide가 BASE_DIR/guides 에 저장한다고 가정하고,
    # 테스트에서는 그 경로에 파일이 생기는지 확인합니다.
    # 더 나은 방법은 generate_guide가 출력 디렉토리도 인자로 받는 것입니다.

    # 우선은 현재 generate_guide의 동작(BASE_DIR/guides/)을 그대로 두고,
    # 테스트용 파일이 생성되는지 확인합니다.
    # 이를 위해 guides 폴더가 테스트 전에 존재하도록 보장하거나, 
    # generate_guide가 폴더를 생성하는지 확인합니다.
    
    # generate_guide가 파일명에 파라미터를 포함시키므로, 예상 파일명을 구성해야 합니다.
    params = SAMPLE_PARAMS_FOR_TEST
    class_name = params.get('class', 'UnknownClass')
    mastery_name = params.get('mastery', 'NoMastery')
    level = params.get('level', 'AnyLevel')
    hc_status = "HC" if params.get('hardcore') else "SC"
    filename_suffix = f"{class_name}_{mastery_name}_L{level}_{hc_status}"
    
    # output_filename_base를 테스트용으로 설정
    output_base_for_this_test = f"pytest_temp_guide_{filename_suffix}"
    
    # generate_guide 호출
    # 참고: generate_guide 함수는 BASE_DIR/guides/ 내에 파일을 생성합니다.
    # 테스트 환경에서는 이를 tmp_path로 바꾸는 것이 이상적입니다.
    # 여기서는 실제 경로에 생성된다고 가정하고 테스트합니다. (테스트 후 정리 필요)
    # 실제로는 monkeypatch로 os.makedirs 등을 모킹하거나, 출력 경로를 제어 가능하게 해야합니다.
    
    # monkeypatch를 사용하여 BASE_DIR을 tmp_path로 변경
    # (단, guide.py의 BASE_DIR 정의 방식에 따라 이 방식이 안 통할 수 있음)
    # monkeypatch.setattr(guide_module, 'BASE_DIR', str(tmp_path)) # guide_module을 임포트해야함

    # 가장 간단한 방법: generate_guide가 절대 경로를 output_filename_base로 받을 수 있다면...
    # 현재 generate_guide는 output_filename_base를 이름으로만 사용하고, 경로는 고정입니다.
    # 테스트를 위해 generate_guide 함수를 약간 수정하거나, 테스트 방식을 바꿔야 합니다.

    # 임시 해결: 테스트용으로 guides 폴더를 사용하되, 파일명을 고유하게 만듭니다.
    guides_dir = os.path.join(BASE_DIR, "guides")
    if not os.path.exists(guides_dir):
        os.makedirs(guides_dir)

    # 파일이 생성될 것으로 예상되는 전체 경로
    # generate_guide 함수는 .pdf 또는 .html을 붙입니다.
    # (현재 generate_guide는 PDF 생성 실패 시 HTML을 생성하므로, 둘 중 하나 또는 둘 다 확인)
    expected_pdf_path = os.path.join(guides_dir, f"{output_base_for_this_test}.pdf")
    expected_html_path = os.path.join(guides_dir, f"{output_base_for_this_test}.html")

    # 함수 호출 (params는 필수)
    returned_path_str = generate_guide(params=SAMPLE_PARAMS_FOR_TEST, output_filename_base=output_base_for_this_test)
    
    assert returned_path_str is not None, "경로가 반환되지 않았습니다."
    returned_path = Path(returned_path_str) # 문자열 경로를 Path 객체로 변환
    
    # 반환된 경로에 실제로 파일이 생성되었는지 확인
    assert returned_path.exists(), f"파일이 생성되지 않았습니다: {returned_path_str}"
    
    # 생성된 파일 확장자 확인 (PDF 또는 HTML)
    assert returned_path.suffix in ['.pdf', '.html'], f"예상치 못한 파일 확장자: {returned_path.suffix}"

    # 테스트 후 생성된 파일 삭제 (선택 사항)
    if returned_path.exists():
        os.remove(returned_path)


def test_generate_guide_default_filename_creation(tmp_path: Path, monkeypatch):
    """
    output_filename_base를 제공하지 않았을 때, generate_guide가 기본 파일명을 사용하는지,
    그리고 params에 따라 파일명이 잘 생성되는지 간접적으로 확인 (파일 생성 여부로)
    """
    if not callable(generate_guide):
        pytest.skip("'generate_guide' 함수를 임포트할 수 없어 테스트를 건너뜁니다.")

    # generate_guide 함수는 BASE_DIR/guides/ 경로에 파일을 생성합니다.
    # 이 테스트에서는 tmp_path를 활용하기 위해 generate_guide의 동작을 변경하거나
    # os.path.join을 모킹해야 하지만, 여기서는 실제 경로에 생성되는 것을 가정합니다.
    guides_dir = os.path.join(BASE_DIR, "guides")
    if not os.path.exists(guides_dir):
        os.makedirs(guides_dir)
        
    # output_filename_base를 생략하여 기본값("build_guide")이 사용되도록 함
    params = SAMPLE_PARAMS_FOR_DEFAULT_TEST
    returned_path_str = generate_guide(params=params) 
    
    assert returned_path_str is not None
    returned_path = Path(returned_path_str)
    assert returned_path.exists()

    # 파일명에 기본 베이스("build_guide")와 params 기반 suffix가 포함되었는지 확인
    class_name = params.get('class', 'UnknownClass')
    mastery_name = params.get('mastery', 'NoMastery') # 이 테스트에서는 mastery가 없을 수 있음
    level = params.get('level', 'AnyLevel')
    hc_status = "HC" if params.get('hardcore') else "SC" # 이 테스트에서는 hardcore가 없을 수 있음
    
    # generate_guide 내부에서 파일명 만들 때 mastery, hardcore가 없으면 기본값 사용하거나 제외함
    # 여기서는 파일명에 class와 level이 포함되는지만 느슨하게 확인
    assert "build_guide" in returned_path.name.lower()
    assert class_name.lower() in returned_path.name.lower()
    assert f"l{level}" in returned_path.name.lower()
    
    if returned_path.exists():
        os.remove(returned_path)

# --- 기존의 테스트 함수들은 인자 전달 방식만 수정 ---
# (아래는 test_generate_guide_default_path를 좀 더 pytest 방식에 맞게 수정한 예시입니다)
# def test_generate_guide_default_path(tmp_path, monkeypatch):
#     # ... (위와 유사하게 params를 정의하고 generate_guide 호출) ...
#     # monkeypatch.chdir(tmp_path) 를 사용하면 현재 작업 디렉토리가 변경되므로,
#     # generate_guide가 상대 경로로 파일을 생성한다면 tmp_path에 생성될 수 있습니다.
#     # 단, generate_guide 내부에서 BASE_DIR을 기준으로 절대 경로를 만들면 chdir은 효과가 없습니다.
