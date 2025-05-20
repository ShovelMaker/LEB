# D:\LEB\src\db_utils.py

import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "resources", "resources.db")
PROCESSED_UNIQUES_PATH = os.path.join(BASE_DIR, "resources", "processed_uniques.json") # 가공된 JSON 파일 경로

FALLBACK_CLASSES_DATA = {"클래스 선택...": [], "Mage": [], "Rogue": [], "Primalist": [], "Acolyte": [], "Sentinel": []}
FALLBACK_UNIQUES_LIST = [] # 원본 및 가공된 데이터 모두 해당
FALLBACK_ITEM_TYPE_MAP = {}
FALLBACK_AFFIX_DATA_MAP = {}

ITEM_TYPES_ENDPOINT = "maxroll/items/itemTypes"
UNIQUES_ENDPOINT = "maxroll/items/uniques" # 원본 고유 아이템 엔드포인트
AFFIXES_ENDPOINT = "maxroll/items/affixes"

def get_classes_from_db():
    conn = None; processed_data = {"클래스 선택...": []} 
    try:
        if not os.path.exists(DB_PATH): print(f"경고: DB 파일({DB_PATH}) 없음 (클래스). 폴백 사용."); return FALLBACK_CLASSES_DATA.copy()
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT data FROM endpoints WHERE endpoint = ?", ("maxroll/items/classes",))
        row = cursor.fetchone()
        if row and row[0]:
            classes_list_from_db = json.loads(row[0]) 
            for class_entry in classes_list_from_db:
                if isinstance(class_entry, dict):
                    base_class_name = class_entry.get("className")
                    masteries_raw = class_entry.get("masteries", [])
                    mastery_names = []
                    if isinstance(masteries_raw, list):
                        for mastery_detail in masteries_raw:
                            if isinstance(mastery_detail, dict):
                                mastery_name = mastery_detail.get("name")
                                loc_key = mastery_detail.get("localizationKey", "")
                                if mastery_name and loc_key.startswith("Mastery_"):
                                    mastery_names.append(mastery_name)
                    if base_class_name: processed_data[base_class_name] = mastery_names
            if len(processed_data) > 1: return processed_data # 성공 시 print는 app_planner에서 하도록 제거
        print("경고: 클래스 DB 데이터 문제. 폴백 사용."); return FALLBACK_CLASSES_DATA.copy()
    except Exception as e: print(f"클래스 데이터 로드 오류: {e}. 폴백 사용."); return FALLBACK_CLASSES_DATA.copy()
    finally:
        if conn: conn.close()

def get_uniques_from_db(): # 원본 고유 아이템 리스트 반환 (scripts/process_game_data.py 용)
    conn = None
    try:
        if not os.path.exists(DB_PATH): return FALLBACK_UNIQUES_LIST[:] 
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT data FROM endpoints WHERE endpoint = ?", (UNIQUES_ENDPOINT,))
        row = cursor.fetchone()
        if row and row[0]:
            uniques_list_from_db = json.loads(row[0]) 
            if isinstance(uniques_list_from_db, list): return uniques_list_from_db
        print(f"경고: '{UNIQUES_ENDPOINT}' 원본 데이터 문제. 폴백 사용."); return FALLBACK_UNIQUES_LIST[:]
    except Exception as e: print(f"원본 고유 아이템 로드 오류: {e}. 폴백 사용."); return FALLBACK_UNIQUES_LIST[:]
    finally:
        if conn: conn.close()

def load_item_type_map_from_db(): # 아이템 유형 이름 맵 반환 (scripts/process_game_data.py 용)
    conn = None; item_type_map = {}
    try:
        if not os.path.exists(DB_PATH): return FALLBACK_ITEM_TYPE_MAP.copy()
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT data FROM endpoints WHERE endpoint = ?", (ITEM_TYPES_ENDPOINT,))
        row = cursor.fetchone()
        if row and row[0]:
            raw_item_types_list = json.loads(row[0])
            if isinstance(raw_item_types_list, list):
                for base_type_entry in raw_item_types_list:
                    if isinstance(base_type_entry, dict):
                        base_id = base_type_entry.get("baseTypeID")
                        base_name = base_type_entry.get("displayName") or base_type_entry.get("BaseTypeName") 
                        if base_id is not None and base_name:
                            str_base_id = str(base_id)
                            item_type_map[str_base_id] = {"name": base_name, "subtypes": {}}
                            sub_items_raw = base_type_entry.get("subItems", [])
                            if isinstance(sub_items_raw, list):
                                for sub_item_entry in sub_items_raw:
                                    if isinstance(sub_item_entry, dict):
                                        sub_id = sub_item_entry.get("subTypeID")
                                        sub_name = sub_item_entry.get("name") or sub_item_entry.get("displayName")
                                        if sub_id is not None and sub_name:
                                            item_type_map[str_base_id]["subtypes"][str(sub_id)] = sub_name
                if item_type_map: return item_type_map
        print(f"경고: '{ITEM_TYPES_ENDPOINT}' 데이터 문제. 폴백 사용."); return FALLBACK_ITEM_TYPE_MAP.copy()
    except Exception as e: print(f"아이템 유형 로드 오류: {e}. 폴백 사용."); return FALLBACK_ITEM_TYPE_MAP.copy()
    finally:
        if conn: conn.close()

def load_raw_affixes_from_db(): # 원본 Affix 리스트 반환 (scripts/process_game_data.py 용)
    conn = None
    try:
        if not os.path.exists(DB_PATH): return FALLBACK_AFFIX_LIST[:]
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT data FROM endpoints WHERE endpoint = ?", (AFFIXES_ENDPOINT,))
        row = cursor.fetchone()
        if row and row[0]:
            raw_affixes_list = json.loads(row[0])
            if isinstance(raw_affixes_list, list): return raw_affixes_list
        print(f"경고: '{AFFIXES_ENDPOINT}' 원본 데이터 문제. 폴백 사용."); return FALLBACK_AFFIX_LIST[:]
    except Exception as e: print(f"원본 옵션(Affix) 데이터 로드 오류: {e}. 폴백 사용."); return FALLBACK_AFFIX_LIST[:]
    finally:
        if conn: conn.close()

# ####################################################################
# # 새로 추가: 가공된 고유 아이템 JSON 파일 로드 함수 (app_planner.py 용)
# ####################################################################
def load_processed_uniques_from_json():
    """
    scripts/process_game_data.py가 생성한 processed_uniques.json 파일에서
    가공된 고유 아이템 목록을 로드하여 반환합니다.
    파일이 없거나 오류 발생 시 빈 리스트를 반환합니다.
    """
    if not os.path.exists(PROCESSED_UNIQUES_PATH):
        print(f"경고: 가공된 고유 아이템 파일({PROCESSED_UNIQUES_PATH})을 찾을 수 없습니다. 빈 리스트를 반환합니다.")
        print("    'scripts/process_game_data.py'를 먼저 실행하여 파일을 생성해야 합니다.")
        return FALLBACK_UNIQUES_LIST[:] # 빈 리스트

    try:
        with open(PROCESSED_UNIQUES_PATH, 'r', encoding='utf-8') as f:
            processed_uniques = json.load(f)
        if isinstance(processed_uniques, list):
            print(f"'{PROCESSED_UNIQUES_PATH}'에서 {len(processed_uniques)}개의 가공된 고유 아이템 정보를 로드했습니다.")
            return processed_uniques
        else:
            print(f"경고: '{PROCESSED_UNIQUES_PATH}' 파일의 형식이 올바르지 않습니다 (리스트가 아님). 빈 리스트를 반환합니다.")
            return FALLBACK_UNIQUES_LIST[:]
    except json.JSONDecodeError as e:
        print(f"'{PROCESSED_UNIQUES_PATH}' JSON 파싱 오류: {e}. 빈 리스트를 반환합니다.")
        return FALLBACK_UNIQUES_LIST[:]
    except Exception as e:
        print(f"'{PROCESSED_UNIQUES_PATH}' 파일 로드 중 예기치 않은 오류: {e}. 빈 리스트를 반환합니다.")
        return FALLBACK_UNIQUES_LIST[:]

# ####################################################################

if __name__ == '__main__':
    print(f"--- '{DB_PATH}'에서 클래스 정보 로딩 테스트 ---")
    loaded_classes = get_classes_from_db(); 
    if loaded_classes and len(loaded_classes) > 1: print(f"클래스 로드 성공: {len(loaded_classes)-1}개")
    else: print("클래스 정보 로딩 실패 또는 데이터 부족.")

    # 아래 함수들은 이제 process_game_data.py에서 주로 사용될 원본 데이터 로더입니다.
    # get_uniques_from_db() 
    # load_item_type_map_from_db()
    # load_raw_affixes_from_db() 

    print(f"\n--- '{PROCESSED_UNIQUES_PATH}'에서 가공된 고유 아이템 정보 로딩 테스트 ---")
    processed_uniques_test = load_processed_uniques_from_json()
    if processed_uniques_test:
        print(f"가공된 고유 아이템 로드 성공: {len(processed_uniques_test)}개")
        print("첫 번째 가공된 아이템 이름 미리보기:")
        print(f"- {processed_uniques_test[0].get('name_display', '이름 없음')}")
    else:
        print("가공된 고유 아이템 정보 로딩에 실패했거나 데이터가 없습니다.")
