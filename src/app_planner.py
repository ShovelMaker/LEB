# D:\LEB\src\app_planner.py

import sys
import os
import json 
import re 
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QTextEdit, QSizePolicy, QSpacerItem,
                             QSpinBox, QCheckBox, QTabWidget, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView 
from PyQt5.QtGui import QDesktopServices 

try:
    from src.guide import generate_guide
except ImportError as e:
    print(f"CRITICAL ERROR: src.guide 모듈을 찾을 수 없습니다: {e}")
    def generate_guide(*args, **kwargs): return "오류: src.guide 모듈 로드 실패."
try:
    from src.crawler import refresh_all
except ImportError as e:
    print(f"CRITICAL ERROR: src.crawler 모듈을 찾을 수 없습니다: {e}")
    def refresh_all(*args, **kwargs): return {'success': False, 'output': "오류: src.crawler 모듈 로드 실패."}
try:
    # 이제 process_unique_item_data는 사용 안함. 가공된 JSON을 직접 로드.
    from src.db_utils import (get_classes_from_db, 
                               load_processed_uniques_from_json, # 새로 추가될 함수
                               FALLBACK_CLASSES_DATA, FALLBACK_UNIQUES_DATA) # FALLBACK_UNIQUES_DATA는 이제 processed 데이터용
except ImportError as e:
    print(f"CRITICAL ERROR: src.db_utils 모듈 또는 함수를 찾을 수 없습니다: {e}")
    FALLBACK_CLASSES_DATA_APP = {"클래스 선택...": [], "Mage": [], "Rogue": [], "Primalist": [], "Acolyte": [], "Sentinel": []}
    def get_classes_from_db(): print("경고: db_utils 사용 불가 - 클래스 폴백 사용."); return FALLBACK_CLASSES_DATA_APP.copy()
    def load_processed_uniques_from_json(): print("경고: db_utils.load_processed_uniques_from_json 사용 불가"); return []


BUILD_TYPES = ["타입 선택...", "스타터 (Starter)", "엔드게임 (Endgame)", "레벨링 (Leveling)"]
GAME_VERSIONS = ["버전 선택...", "최신 패치 (Latest)", "1.1.x", "1.0.x"]

class GuideGenerationWorker(QObject):
    # ... (이전과 동일) ...
    finished = pyqtSignal(str); error = pyqtSignal(str); progress = pyqtSignal(str)
    def __init__(self, params, output_filename_base):
        super().__init__(); self.params = params; self.output_filename_base = output_filename_base
    def run(self):
        try:
            self.progress.emit("LLM 가이드 생성을 시작합니다...")
            result_path = generate_guide(self.params, self.output_filename_base)
            if result_path and "오류:" not in result_path:
                if os.path.exists(result_path) and os.path.getsize(result_path) > 0: self.finished.emit(result_path)
                else: self.error.emit(f"파일 생성 실패 또는 빈 파일: {result_path}")
            elif result_path and "오류:" in result_path: self.error.emit(result_path)
            else: self.error.emit(f"알 수 없는 오류 또는 파일 생성 실패: {result_path if result_path else '결과 없음'}")
        except Exception as e: self.error.emit(f"가이드 생성 스레드 오류: {e}")

class RefreshWorker(QObject):
    # ... (이전과 동일) ...
    finished = pyqtSignal(dict); progress = pyqtSignal(str) 
    def __init__(self): super().__init__()
    def run(self):
        try:
            result_dict = refresh_all(); self.finished.emit(result_dict)
        except Exception as e:
            self.progress.emit(f"새로고침 스레드 오류: {e}")
            self.finished.emit({'success': False, 'output': f"새로고침 스레드 오류: {e}"})

class PlannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget) 
        self.guide_generation_thread = None; self.guide_worker = None
        self.refresh_thread = None; self.refresh_worker = None

        self.log_message_initial("DB/JSON 데이터 로딩 시작...") 
        self.game_class_data = get_classes_from_db() # 이건 여전히 DB에서 직접
        # ####################################################################
        # # 가공된 고유 아이템 데이터를 JSON 파일에서 로드
        # ####################################################################
        self.all_processed_unique_items = load_processed_uniques_from_json() 
        # self.item_type_map, self.affix_data_map은 이제 app_planner에서 직접 사용 안 함
        # ####################################################################
        self.log_message_initial("DB/JSON 데이터 로딩 완료.")
        
        if not self.game_class_data or len(self.game_class_data) <= 1 :
             if "FALLBACK_CLASSES_DATA_APP" in globals(): 
                self.log_message_initial("경고: 클래스 데이터 로드 실패. 앱 내 폴백 사용.")
                self.game_class_data = FALLBACK_CLASSES_DATA_APP.copy()
             else: self.log_message_initial("CRITICAL: 클래스 데이터 로드 완전 실패."); self.game_class_data = {"클래스 선택...": []}
        if not self.all_processed_unique_items: self.log_message_initial("경고: 가공된 고유 아이템 데이터 로드 실패.")
        
        self.initUI() 
        self.setWindowTitle("Last Epoch Build Planner (LEB) - v0.8 (Data Refactor)") 
        self.setGeometry(100, 100, 1366, 768) 

    def log_message_initial(self, message): print(f"INITIAL LOG: {message}")

    def initUI(self):
        # ... (UI 구성은 이전과 거의 동일) ...
        self.left_panel = QWidget(); self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding) 
        self.left_panel.setMinimumWidth(300); self.left_panel.setMaximumWidth(380) 
        control_layout = QVBoxLayout(self.left_panel)
        self.right_tab_widget = QTabWidget()
        self.log_tab = QWidget(); log_layout = QVBoxLayout(self.log_tab)
        self.log_edit = QTextEdit(); self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        self.right_tab_widget.addTab(self.log_tab, "📜 로그")
        self.guide_view_tab = QWidget(); guide_view_layout = QVBoxLayout(self.guide_view_tab)
        self.guide_view = QWebEngineView(); guide_view_layout.addWidget(self.guide_view)
        self.right_tab_widget.addTab(self.guide_view_tab, "📖 생성된 가이드")
        self.item_compendium_tab = QWidget(); item_compendium_layout = QHBoxLayout(self.item_compendium_tab) 
        self.unique_item_list_widget = QListWidget(); self.unique_item_list_widget.currentItemChanged.connect(self.display_unique_item_details)
        item_compendium_layout.addWidget(self.unique_item_list_widget, 1) 
        self.unique_item_detail_text = QTextEdit(); self.unique_item_detail_text.setReadOnly(True)
        self.unique_item_detail_text.setLineWrapMode(QTextEdit.NoWrap) 
        item_compendium_layout.addWidget(self.unique_item_detail_text, 2) 
        self.right_tab_widget.addTab(self.item_compendium_tab, "💎 아이템 도감 (고유)")
        self.refresh_button = QPushButton("🔄 데이터 새로고침"); self.refresh_button.clicked.connect(self.handle_refresh_async)
        control_layout.addWidget(self.refresh_button)
        self.version_banner_label = QLabel("(버전 정보)"); self.version_banner_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.version_banner_label)
        self.perform_version_check() 
        self.class_label = QLabel("기본 클래스:"); control_layout.addWidget(self.class_label)
        self.class_combo = QComboBox()
        if self.game_class_data and len(self.game_class_data) > 1:
            for base_class in self.game_class_data.keys(): self.class_combo.addItem(base_class)
        else: self.class_combo.addItem("클래스 로드 실패"); self.log_message("오류: 클래스 목록 로드 실패.")
        self.class_combo.currentIndexChanged.connect(self.update_masteries); control_layout.addWidget(self.class_combo)
        self.mastery_label = QLabel("마스터리:"); control_layout.addWidget(self.mastery_label)
        self.mastery_combo = QComboBox(); self.mastery_combo.addItem("마스터리 선택..."); self.mastery_combo.setEnabled(False)
        control_layout.addWidget(self.mastery_combo)
        self.level_label = QLabel("캐릭터 레벨 (1-100):"); control_layout.addWidget(self.level_label)
        self.level_spinbox = QSpinBox(); self.level_spinbox.setRange(1, 100); self.level_spinbox.setValue(1)
        control_layout.addWidget(self.level_spinbox)
        self.hc_checkbox = QCheckBox("하드코어 모드 (HC)"); control_layout.addWidget(self.hc_checkbox)
        self.build_type_label = QLabel("빌드 타입:"); control_layout.addWidget(self.build_type_label)
        self.build_type_combo = QComboBox(); self.build_type_combo.addItems(BUILD_TYPES)
        control_layout.addWidget(self.build_type_combo)
        self.game_version_label = QLabel("게임 버전:"); control_layout.addWidget(self.game_version_label)
        self.game_version_combo = QComboBox(); self.game_version_combo.addItems(GAME_VERSIONS)
        control_layout.addWidget(self.game_version_combo)
        control_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.generate_button = QPushButton("▶ 가이드 생성"); self.generate_button.clicked.connect(self.handle_generate_guide_async)
        control_layout.addWidget(self.generate_button)
        self.main_layout.addWidget(self.left_panel, 1) 
        self.main_layout.addWidget(self.right_tab_widget, 3)
        
        self.populate_processed_unique_item_list() # 이름 변경
        self.log_message("프로그램 UI 초기화 완료.")
        self.update_masteries()

    def log_message(self, message):
        if hasattr(self, 'log_edit') and self.log_edit: self.log_edit.append(str(message))
        else: print(f"LOG: {message}")

    def populate_processed_unique_item_list(self): # 이름 변경
        self.unique_item_list_widget.clear()
        if self.all_processed_unique_items: # 가공된 데이터 사용
            # 이름으로 정렬 (이미 name_display로 가공됨)
            sorted_items = sorted(self.all_processed_unique_items, key=lambda x: x.get('name_display', ''))
            for item_data in sorted_items: # 이제 item_data는 가공된 딕셔너리
                display_name = item_data.get('name_display', '이름 없음')
                list_item = QListWidgetItem(display_name)
                # QListWidgetItem에 저장하는 데이터도 이제 가공된 item_data 전체
                list_item.setData(Qt.UserRole, item_data) 
                self.unique_item_list_widget.addItem(list_item)
            self.log_message(f"{len(self.all_processed_unique_items)}개의 가공된 고유 아이템 목록을 UI에 로드했습니다.")
        else:
            self.unique_item_list_widget.addItem("로드된 아이템 없음")
            self.log_message("경고: UI에 로드할 가공된 고유 아이템 데이터가 없습니다.")
            
    def display_unique_item_details(self, current_item_widget, previous_item_widget):
        if not current_item_widget:
            self.unique_item_detail_text.setHtml("<p style='padding:10px; color: #bdc3c7;'>아이템 목록에서 아이템을 선택하세요.</p>")
            return
        
        # 이제 item_data는 process_game_data.py가 생성한 "가공된" 딕셔너리입니다.
        processed_item_data = current_item_widget.data(Qt.UserRole) 
        if not processed_item_data:
            self.unique_item_detail_text.setHtml("<p style='padding:10px; color: #bdc3c7;'>선택된 아이템 정보를 불러올 수 없습니다.</p>")
            return

        item_name_display = processed_item_data.get('name_display', 'N/A')
        level_req = processed_item_data.get('level_requirement', 'N/A')
        item_type_display = processed_item_data.get('item_type_display_full', 'N/A')
        base_item_name_header = processed_item_data.get('item_type_display_base', '아이템').upper()
        lore_html = processed_item_data.get('lore_text', '').replace('\r\n','<br/>').replace('\n','<br/>') # 혹시 모를 재처리
        
        details_html = f"""
        <body style='font-family: "Malgun Gothic", Arial, sans-serif; font-size: 9.5pt; color: #ddeeff; background-color: #2c3e50; padding:15px;'>
            <h2 style='font-size: 1.7em; color: #e67e22; margin-bottom: 0px; padding-bottom: 0px;'>{item_name_display}</h2>
            <p style='font-size: 0.9em; color: #e67e22; margin-top: 0px; margin-bottom: 2px;'>UNIQUE {base_item_name_header}</p>
            <p style='font-size: 0.9em; color: #bdc3c7; margin-top: 0px; margin-bottom: 10px;'>
                <b>요구 레벨:</b> {level_req} 
                {f"| <b>세부 유형:</b> {item_type_display}" if item_type_display != base_item_name_header else ""}
            </p>
            <hr style='border: 0; border-top: 1px dashed #4a6278; margin: 15px 0;'/>"""
        
        # 명시적 옵션 표시 (가공된 리스트 사용)
        formatted_mods_list = processed_item_data.get('formatted_mods_list', [])
        if formatted_mods_list:
            details_html += f"<h3 style='font-size: 1.1em; color: #3498db; margin-top:15px; margin-bottom: 8px;'>명시적 옵션:</h3><ul style='padding-left: 20px; margin-top: 0px; list-style-type: \"\\25CF\"; color: #A9D18E;'>"
            for mod_line_text in formatted_mods_list: # 이제 이미 완성된 텍스트 라인
                details_html += f"<li style='margin-bottom: 4px;'>{mod_line_text}</li>"
            details_html += "</ul><hr style='border: 0; border-top: 1px dashed #4a6278; margin: 10px 0 15px 0;'/>"
        
        # 고유 효과 표시 (가공된 리스트 사용)
        formatted_tooltips_list = processed_item_data.get('formatted_tooltips_list', [])
        if formatted_tooltips_list:
            details_html += f"<h3 style='font-size: 1.1em; color: #FFBF00; margin-bottom: 8px;'>고유 효과:</h3><div style='padding-left: 10px; border-left: 3px solid #FFBF00; margin-bottom: 15px; background-color: #34495e; padding: 10px; border-radius: 3px;'>"
            for tooltip_entry in formatted_tooltips_list:
                desc = tooltip_entry.get("description","").replace('\r\n','<br/>').replace('\n','<br/>')
                alt_text = tooltip_entry.get("altText","").replace('\r\n','<br/>').replace('\n','<br/>')
                details_html += f"<p style='margin: 4px 0; color: #ecf0f1;'>{desc}</p>"
                if alt_text: 
                    details_html += f"<p style='font-size:0.85em; color:#95a5a6; margin-top: 2px; margin-bottom: 8px;'><i>({alt_text})</i></p>"
            details_html += "</div>"
        
        if lore_html: 
            details_html += f"<h3 style='font-size: 1.1em; color: #9b59b6; margin-top:15px; margin-bottom: 8px;'>이야기:</h3><p style='font-style: italic; color: #bdc3c7;'>{lore_html}</p>"
        details_html += "</body>"
        
        self.unique_item_detail_text.setHtml(details_html)
        self.log_message(f"'{item_name_display}' 아이템 상세 정보를 표시합니다 (가공된 데이터 사용).")

    def update_masteries(self):
        # ... (이전과 동일) ...
        selected_class = self.class_combo.currentText(); self.mastery_combo.clear()
        if hasattr(self, 'game_class_data') and self.game_class_data:
            if selected_class and selected_class not in ["클래스 선택...", "클래스 로드 실패"]:
                masteries = self.game_class_data.get(selected_class, [])
                if masteries: self.mastery_combo.addItem("마스터리 선택..."); [self.mastery_combo.addItem(m) for m in masteries]; self.mastery_combo.setEnabled(True)
                else: self.mastery_combo.addItem("선택 가능한 마스터리 없음"); self.mastery_combo.setEnabled(False)
            else: 
                self.mastery_combo.addItem("마스터리 선택..."); self.mastery_combo.setEnabled(False)
                if selected_class == "클래스 선택..." and self.sender() is not None: self.log_message("기본 클래스를 선택해주세요.")
        else: self.mastery_combo.addItem("데이터 로드 오류"); self.mastery_combo.setEnabled(False)

    def handle_refresh_async(self): 
        # ... (이전과 동일) ...
        if self.refresh_thread and self.refresh_thread.isRunning(): self.log_message("이미 데이터 새로고침 중"); return
        self.log_message("데이터 새로고침을 시작합니다..."); self.refresh_button.setEnabled(False); self.right_tab_widget.setCurrentWidget(self.log_tab)
        self.refresh_thread = QThread(); self.refresh_worker = RefreshWorker()
        self.refresh_worker.moveToThread(self.refresh_thread)
        self.refresh_worker.progress.connect(self.log_message); self.refresh_worker.finished.connect(self.on_refresh_finished)
        self.refresh_thread.started.connect(self.refresh_worker.run)
        self.refresh_worker.finished.connect(self.refresh_thread.quit)
        self.refresh_thread.finished.connect(self.refresh_worker.deleteLater); self.refresh_thread.finished.connect(self.refresh_thread.deleteLater)
        self.refresh_thread.finished.connect(lambda: self.refresh_button.setEnabled(True)) 
        self.refresh_thread.start()

    def on_refresh_finished(self, result_dict):
        self.log_message("데이터 새로고침 작업 완료.")
        if result_dict and isinstance(result_dict, dict): 
            if result_dict.get('output'): self.log_message("--- 새로고침 결과 ---"); self.log_message(result_dict['output'])
            if result_dict.get('success'):
                self.log_message("DB 업데이트 성공. UI 데이터 다시 로드...")
                current_class_selection = self.class_combo.currentText()
                self.game_class_data = get_classes_from_db(); self.class_combo.clear()
                if self.game_class_data and len(self.game_class_data) > 1:
                    for base_class in self.game_class_data.keys(): self.class_combo.addItem(base_class)
                    if current_class_selection in self.game_class_data and current_class_selection not in ["클래스 선택...", "클래스 로드 실패"]:
                        self.class_combo.setCurrentText(current_class_selection)
                    else: self.class_combo.setCurrentIndex(0) 
                else: self.class_combo.addItem("클래스 로드 실패")
                self.update_masteries()
                
                # ############################################################
                # # 가공된 데이터 다시 로드
                # ############################################################
                self.all_processed_unique_items = load_processed_uniques_from_json()
                self.populate_processed_unique_item_list() # 이름 변경된 함수 호출
                if not self.all_processed_unique_items: self.log_message("경고: 새로고침 후 가공된 고유 아이템 데이터 로드 실패.")
                # item_type_map, affix_data_map은 process_game_data.py가 실행될 때 사용되므로,
                # app_planner에서는 새로고침 시 다시 로드할 필요가 없습니다.
                # (process_game_data.py를 실행해야 이 맵들도 최신화됨)
                # ############################################################
            else: self.log_message("DB 업데이트 실패. 로그 확인.")
        else: self.log_message("새로고침 결과 비정상.")


    def handle_generate_guide_async(self):
        # ... (이전과 동일) ...
        if self.guide_generation_thread and self.guide_generation_thread.isRunning(): self.log_message("이미 가이드 생성 중."); return
        base_class = self.class_combo.currentText(); mastery = self.mastery_combo.currentText()
        level = self.level_spinbox.value(); is_hardcore = self.hc_checkbox.isChecked()
        build_type = self.build_type_combo.currentText(); game_version = self.game_version_combo.currentText()
        params = {
            "class": base_class if base_class not in ["클래스 선택...", "클래스 로드 실패"] else None,
            "mastery": mastery if mastery not in ["마스터리 선택...", "선택 가능한 마스터리 없음"] else None,
            "level": level, "hardcore": is_hardcore,
            "build_type": build_type if build_type != "타입 선택..." else None,
            "game_version": game_version if game_version != "버전 선택..." else None,
        }
        self.log_message(f"가이드 생성 요청 (파라미터: {params})..."); self.generate_button.setEnabled(False)
        self.right_tab_widget.setCurrentWidget(self.log_tab)
        self.guide_generation_thread = QThread(); output_base = "LE_Guide" 
        self.guide_worker = GuideGenerationWorker(params, output_base)
        self.guide_worker.moveToThread(self.guide_generation_thread)
        self.guide_worker.progress.connect(self.log_message); self.guide_worker.finished.connect(self.on_guide_generation_finished); self.guide_worker.error.connect(self.on_guide_generation_error)
        self.guide_generation_thread.started.connect(self.guide_worker.run)
        self.guide_worker.finished.connect(self.guide_generation_thread.quit); self.guide_worker.error.connect(self.guide_generation_thread.quit)  
        self.guide_generation_thread.finished.connect(self.guide_worker.deleteLater) ; self.guide_generation_thread.finished.connect(self.guide_generation_thread.deleteLater)
        self.guide_generation_thread.finished.connect(lambda: self.generate_button.setEnabled(True)) 
        self.guide_generation_thread.start()

    def on_guide_generation_finished(self, result_path):
        # ... (이전과 동일) ...
        self.log_message(f"가이드 생성 완료. 결과 경로: {result_path}")
        if result_path and "오류:" not in result_path and os.path.exists(result_path):
            absolute_path = os.path.abspath(result_path) 
            if result_path.endswith(".html"):
                self.guide_view.setUrl(QUrl.fromLocalFile(absolute_path)) 
                self.right_tab_widget.setCurrentWidget(self.guide_view_tab) 
                self.log_message(f"'{absolute_path}' HTML 가이드를 뷰어에 표시합니다.")
            elif result_path.endswith(".pdf"): 
                pdf_link = QUrl.fromLocalFile(absolute_path).toString()
                message_html = f"""<html><body style="font-family: sans-serif; padding: 20px;"><h2>PDF 가이드 저장 완료</h2><p>PDF 가이드가 다음 경로에 저장되었습니다:</p><p><a href="{pdf_link}">{absolute_path}</a></p><p>해당 경로에서 직접 파일을 열어 확인해주세요.</p><p>(프로그램 내 직접 표시는 HTML 가이드만 우선 지원됩니다.)</p></body></html>"""
                self.guide_view.setHtml(message_html)
                self.right_tab_widget.setCurrentWidget(self.guide_view_tab)
                self.log_message(f"PDF 가이드가 '{absolute_path}'에 저장되었습니다. '생성된 가이드' 탭에서 경로를 확인하고 직접 열어보세요.")
            else:
                self.log_message(f"알 수 없는 파일 형식입니다: {absolute_path}")
                self.guide_view.setHtml(f"<p>알 수 없는 파일 형식입니다: {absolute_path}</p>"); self.right_tab_widget.setCurrentWidget(self.guide_view_tab)
        elif result_path and "오류:" in result_path:
             self.log_message(f"가이드 생성 중 오류 반환: {result_path}")
             self.guide_view.setHtml(f"<h2>가이드 생성 실패</h2><p>{result_path}</p>"); self.right_tab_widget.setCurrentWidget(self.guide_view_tab)
        else:
            self.log_message(f"가이드 파일 경로 문제: {result_path if result_path else '결과 없음'}")
            self.guide_view.setHtml(f"<h2>결과 없음</h2><p>가이드 파일을 찾을 수 없습니다.</p>"); self.right_tab_widget.setCurrentWidget(self.guide_view_tab)

    def on_guide_generation_error(self, error_message):
        # ... (이전과 동일) ...
        self.log_message(f"가이드 생성 중 명시적 오류: {error_message}")
        self.guide_view.setHtml(f"<h2>가이드 생성 오류</h2><p>{error_message}</p>"); self.right_tab_widget.setCurrentWidget(self.guide_view_tab)

    def perform_version_check(self):
        # ... (이전과 동일) ...
        self.log_message("버전 체크를 수행합니다 (실제 기능 연결 필요)...")
        self.log_message("버전 체크 기능은 아직 연결되지 않았습니다.")
        self.version_banner_label.setText("(버전 체크 기능 연결 필요)")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlannerWindow()
    window.show()
    sys.exit(app.exec_())
