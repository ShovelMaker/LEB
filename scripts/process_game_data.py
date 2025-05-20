# D:\LEB\scripts\process_game_data.py

import json
import os
import sys
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
RESOURCES_DIR = os.path.join(PROJECT_ROOT, 'resources') 

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from db_utils import (get_uniques_from_db, load_item_type_map_from_db, 
                           load_raw_affixes_from_db, # 수정됨!
                           FALLBACK_UNIQUES_DATA, FALLBACK_ITEM_TYPE_MAP, FALLBACK_AFFIX_LIST)
except ImportError as e:
    print(f"오류: src.db_utils 모듈 임포트 실패: {e}"); sys.exit(1)

PROCESSED_UNIQUES_FILE = os.path.join(RESOURCES_DIR, 'processed_uniques.json')

def find_affix_description(raw_affixes_list, property_id, special_tag=None, value_for_scaling=None):
    """
    주어진 property_id, special_tag에 가장 적합한 affix 설명을 raw_affixes_list에서 찾습니다.
    설명 문자열 내의 플레이스홀더 {0}, {1} 등을 value_for_scaling로 대체할 수 있습니다.
    """
    best_match_description = None
    best_match_name = f"Property ID {property_id}" # 기본값
    
    # 1순위: property와 specialTag가 모두 일치하는 affix의 description 필드 (가장 구체적)
    if special_tag is not None:
        for affix in raw_affixes_list:
            if affix.get("property") == property_id and affix.get("specialTag") == special_tag:
                if affix.get("description"): # 설명이 있다면 최우선
                    best_match_description = affix["description"]
                    best_match_name = affix.get("affixDisplayName") or affix.get("affixName") or best_match_name
                    break 
                # 설명이 없더라도 이름은 가져올 수 있음
                current_name = affix.get("affixDisplayName") or affix.get("affixName")
                if current_name: best_match_name = current_name
    
    # 2순위: specialTag 없이 property만 일치하는 것 중 가장 일반적인 이름과, 혹시 있다면 description
    if not best_match_description: # 아직 설명을 못 찾았다면
        candidate_name = None
        candidate_desc = None
        for affix in raw_affixes_list:
            if affix.get("property") == property_id:
                # 이름 선택 로직 (db_utils의 load_affix_data_map_from_db와 유사하게)
                display_name = affix.get("affixDisplayName", "").strip()
                name = affix.get("affixName", "").strip()
                temp_chosen_name = display_name if display_name else name
                
                # description이 있는 경우, 해당 affix의 이름을 우선 사용
                if affix.get("description"):
                    candidate_desc = affix["description"]
                    candidate_name = temp_chosen_name
                    break # 설명이 있으면 바로 사용

                if not candidate_name or \
                   (temp_chosen_name and len(temp_chosen_name) < len(candidate_name) and "idol" not in temp_chosen_name.lower()): # 더 짧고 일반적인 이름
                    candidate_name = temp_chosen_name
        
        if candidate_desc: best_match_description = candidate_desc
        if candidate_name: best_match_name = candidate_name # 이름은 업데이트

    # 설명 문자열 포맷팅 (값이 있다면)
    if best_match_description and value_for_scaling is not None:
        # 예시: "Grants you {0} Ward" -> "Grants you 100 Ward"
        # 값의 부호나 %는 format_mod_value_for_processing에서 처리하므로 여기선 값만 전달
        # 이 부분은 실제 description 문자열의 플레이스홀더 형식에 맞춰야 합니다.
        # 지금은 간단히 {0}만 처리. 더 많은 플레이스홀더({1} 등)가 있다면 추가 처리 필요.
        try:
            # 값이 정수형태로 표시되어야 하는지, 아니면 float 그대로인지 판단 필요.
            # 일단은 float 그대로 넣고, 나중에 string format에서 .0 제거 등을 고려.
            best_match_description = best_match_description.format(value_for_scaling)
        except (IndexError, KeyError, TypeError):
            # 포맷팅 실패 시 원본 설명 사용
            pass 
            
    return best_match_description, best_match_name


def process_and_save_uniques(raw_uniques_data, item_type_map, raw_affixes_list):
    if not raw_uniques_data: print("가공할 원본 고유 아이템 데이터가 없습니다."); return False
    print(f"{len(raw_uniques_data)}개의 고유 아이템 데이터 가공을 시작합니다...")
    processed_items_list = []

    for item_data in raw_uniques_data:
        if not isinstance(item_data, dict): continue
        processed_item = {
            "unique_id": item_data.get("uniqueID"),
            "name_display": item_data.get('displayName') or item_data.get('name', 'N/A'),
            "level_requirement": item_data.get('levelRequirement', 'N/A'),
            "lore_text": item_data.get('loreText', ''), 
        }
        base_type_id_str = str(item_data.get('baseType', 'N/A'))
        sub_type_ids = item_data.get('subTypes', [])
        sub_type_id_str = str(sub_type_ids[0]) if sub_type_ids else None
        item_type_display = f"BaseType ID: {base_type_id_str}"; base_item_name_for_header = "아이템" 
        if item_type_map and base_type_id_str in item_type_map:
            base_type_info = item_type_map[base_type_id_str]
            base_type_name_for_unique = base_type_info.get('name', f"BaseID {base_type_id_str}")
            base_item_name_for_header = base_type_name_for_unique
            if sub_type_id_str and sub_type_id_str in base_type_info.get("subtypes", {}):
                sub_type_name = base_type_info["subtypes"][sub_type_id_str]
                item_type_display = f"{sub_type_name} ({base_type_name_for_unique})"
            else: item_type_display = base_type_name_for_unique
        processed_item['item_type_display_full'] = item_type_display
        processed_item['item_type_display_base'] = base_item_name_for_header.upper()

        formatted_tooltips_list = []
        if item_data.get("tooltipDescriptions"):
            for desc_entry in item_data["tooltipDescriptions"]:
                desc = desc_entry.get('description', '')
                desc = re.sub(r'\[([\d.-]+),\s*([\d.-]+),\s*([\d.-]+)\]%', r'(\1 ~ \2)%', desc)
                desc = re.sub(r'\[([\d.-]+),\s*c,\s*([\d.-]*)\]%', r'\1%', desc) 
                desc = re.sub(r'\[([\d.-]+)\]', r'\1', desc) 
                formatted_tooltips_list.append({"description": desc, "altText": desc_entry.get('altText', '')})
        processed_item['formatted_tooltips_html_list'] = formatted_tooltips_list # HTML 변환은 UI에서

        formatted_mods_list = []
        if item_data.get("mods"):
            for mod in item_data["mods"]:
                if mod.get("hideInTooltip"): continue
                prop_id = mod.get('property')
                special_tag = mod.get('specialTag')
                value = mod.get('value'); max_value = mod.get('maxValue'); 
                can_roll = mod.get('canRoll', False) if max_value is not None else False
                mod_from_unique_type = mod.get('type', 0)
                mod_tags = mod.get('tags', 0) 

                # affixes.json에서 설명 및 기본 이름 찾아오기
                # 이 부분은 find_affix_description으로 대체되거나, 이 함수가 더 정교한 이름을 찾아야 함.
                # 여기서는 우선 property ID에 대한 기본 이름을 가져오는 것으로 가정 (이전 db_utils.load_affix_data_map_from_db 결과)
                # 이 부분은 실제 affixes.json 구조와 find_affix_description 함수에 맞춰야 합니다.
                # 임시: affix_data_map은 property_id -> 이름 형태라고 가정.
                # 실제로는 (property_id, special_tag)로 검색하거나, affix_id로 검색해야 할 수 있음.
                
                full_description, base_mod_name = find_affix_description(raw_affixes_list, prop_id, special_tag, value)

                final_mod_name = base_mod_name # find_affix_description에서 찾은 이름
                minion_keywords = ["minion", "companion", "totem", "pet", "summon", "골렘", "스켈레톤", "레이스", "비스트"]
                is_minion_mod_by_tag = (mod_tags == 8192)
                if is_minion_mod_by_tag and not any(kw in final_mod_name.lower() for kw in minion_keywords):
                     final_mod_name = f"Minion {final_mod_name}"
                if str(prop_id) == "88": final_mod_name = "to All Minion Skills" if is_minion_mod_by_tag else "to All Skills"
                
                value_str_formatted = ""
                if full_description: # affixes.json에 완전한 설명이 있다면 그것을 사용
                    # full_description 내에 값 플레이스홀더가 있고, value/maxValue로 포맷팅 필요
                    # 예시: "{0} to {1} Fire Damage" -> value, maxValue 사용
                    # 지금은 간단히 full_description을 그대로 사용. 포맷팅은 추후 정교화.
                    # 만약 full_description이 이미 값까지 포함된 형태라면 아래 값 포맷팅은 필요 없음.
                    # 여기서는 full_description이 순수 텍스트이고, 값은 따로 포맷팅 한다고 가정.
                    if value is not None: # 값이 있는 경우에만 값 포맷팅 추가
                        # (아래 값 포맷팅 로직은 유지)
                        is_percentage = mod_from_unique_type in [1, 2]
                        def format_value_for_processing(val, is_percent_type, mod_type):
                            _prefix = ""
                            if mod_type == 0 and isinstance(val, (int, float)) and val > 0: _prefix = "+"
                            _suffix = "%" if is_percent_type else ""
                            num_str = ""
                            if isinstance(val, float):
                                num_to_format = val * 100 if is_percent_type else val
                                num_str = f"{num_to_format:.1f}".replace(".0", "")
                            else: num_str = str(int(val * 100)) if is_percent_type else str(val)
                            return f"{_prefix}{num_str}{_suffix}"
                        value_display = format_value_for_processing(value, is_percentage, mod_from_unique_type)
                        if can_roll and max_value is not None and value != max_value:
                            max_value_display = format_value_for_processing(max_value, is_percentage, mod_from_unique_type)
                            value_str_formatted = f"({value_display} ~ {max_value_display.lstrip('+')})"
                        else: value_str_formatted = value_display
                        final_mod_name = f"{value_str_formatted} {full_description}" # 설명이 있다면 값을 앞에 붙임
                    else: # 값이 없는 서술형 옵션
                        final_mod_name = full_description
                    formatted_mods_list.append(final_mod_name) # 이미 완전한 문장
                    continue # 다음 mod로

                # full_description이 없는 일반적인 경우 (이름 + 값 포맷팅)
                if value is not None:
                    # (이전 값 포맷팅 로직과 동일)
                    is_percentage = mod_from_unique_type in [1, 2]
                    def format_value_for_processing(val, is_percent_type, mod_type):
                        _prefix = ""
                        if mod_type == 0 and isinstance(val, (int, float)) and val > 0: _prefix = "+"
                        _suffix = "%" if is_percent_type else ""
                        num_str = ""
                        if isinstance(val, float):
                            num_to_format = val * 100 if is_percent_type else val
                            num_str = f"{num_to_format:.1f}".replace(".0", "")
                        else: num_str = str(int(val * 100)) if is_percent_type else str(val)
                        return f"{_prefix}{num_str}{_suffix}"
                    value_display = format_value_for_processing(value, is_percentage, mod_from_unique_type)
                    if can_roll and max_value is not None and value != max_value:
                        max_value_display = format_value_for_processing(max_value, is_percentage, mod_from_unique_type)
                        value_str_formatted = f"({value_display} ~ {max_value_display.lstrip('+')})"
                    else: value_str_formatted = value_display
                
                type_description = ""
                if value is not None and mod_from_unique_type !=0 : 
                    if mod_from_unique_type == 1: type_description = " Increased" if (value >= 0) else " Reduced"
                    elif mod_from_unique_type == 2: type_description = " More" if (value >= 0) else " Less"
                    if type_description.strip().lower() in final_mod_name.lower(): type_description = ""
                
                mod_line = ""
                if str(prop_id) == "88" and value is not None: mod_line = f"{value_str_formatted} {final_mod_name}"
                elif value is not None: mod_line = f"{value_str_formatted} {final_mod_name}{type_description}"
                else: mod_line = final_mod_name
                formatted_mods_list.append(mod_line)
        processed_item['formatted_mods_list'] = formatted_mods_list
        processed_items_list.append(processed_item)

    try:
        if not os.path.exists(RESOURCES_DIR): os.makedirs(RESOURCES_DIR)
        with open(PROCESSED_UNIQUES_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed_items_list, f, indent=4, ensure_ascii=False)
        print(f"가공된 고유 아이템 데이터 {len(processed_items_list)}개를 '{PROCESSED_UNIQUES_FILE}'에 저장했습니다.")
        return True
    except Exception as e: print(f"고유 아이템 데이터 가공/저장 오류: {e}"); return False

def main():
    print("게임 데이터 가공을 시작합니다...")
    print("DB에서 원본 데이터를 로드합니다...")
    raw_uniques = get_uniques_from_db()
    item_type_map = load_item_type_map_from_db()
    raw_affixes_list = load_raw_affixes_from_db() # 수정됨!

    if not raw_uniques or not item_type_map or not raw_affixes_list: # 수정됨!
        print("데이터 가공 필요 원본 데이터 로드 실패. 작업 중단."); return
    process_and_save_uniques(raw_uniques, item_type_map, raw_affixes_list) # 수정됨!
    print("모든 데이터 가공 작업이 완료되었습니다.")

if __name__ == '__main__':
    main()
