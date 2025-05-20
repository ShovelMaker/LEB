#!/usr/bin/env python3
import sys
import os
import threading
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTextEdit, QTabWidget
)

# 프로젝트 루트(상위 디렉터리)를 모듈 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# crawler 모듈 import
try:
    from crawler import refresh_all
except ImportError:
    logging.critical('crawler 모듈을 찾을 수 없습니다. src/crawler.py 경로를 확인하세요.')
    sys.exit(1)

# guide 모듈 import
try:
    from guide import generate_guide
except ImportError:
    logging.critical('guide 모듈을 찾을 수 없습니다. src/guide.py 경로를 확인하세요.')
    sys.exit(1)

# QTextEdit에 로그를 출력하기 위한 핸들러 정의
class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.widget = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class PlannerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LEB Planner')
        self.resize(800, 600)

        # 메인 레이아웃 설정
        main_layout = QHBoxLayout(self)
        control_layout = QVBoxLayout()

        # 로그 출력용 QTextEdit
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # Refresh 버튼
        self.btn_refresh = QPushButton('🔄 Refresh')
        self.btn_refresh.clicked.connect(self.on_refresh_clicked)
        control_layout.addWidget(self.btn_refresh)

        # Generate Guide 버튼
        self.btn_generate = QPushButton('▶ Generate Guide')
        self.btn_generate.clicked.connect(self.on_generate_clicked)
        control_layout.addWidget(self.btn_generate)

        control_layout.addStretch()
        main_layout.addLayout(control_layout, 1)

        # 로그 탭
        tabs = QTabWidget()
        tabs.addTab(self.log_output, 'Log')
        main_layout.addWidget(tabs, 3)

        # 로깅 설정
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = QTextEditLogger(self.log_output)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def on_refresh_clicked(self):
        self.btn_refresh.setEnabled(False)
        threading.Thread(target=self.run_refresh, daemon=True).start()

    def run_refresh(self):
        success = refresh_all()
        # 메인 스레드에서 버튼 재활성화
        self.btn_refresh.setEnabled(True)
        if success:
            logging.info('리소스 업데이트가 완료되었습니다.')
        else:
            logging.error('리소스 업데이트에 실패했습니다.')

    def on_generate_clicked(self):
        self.btn_generate.setEnabled(False)
        threading.Thread(target=self.run_generate, daemon=True).start()

    def run_generate(self):
        path = generate_guide()
        # 버튼 재활성화
        self.btn_generate.setEnabled(True)
        if path:
            logging.info(f'가이드가 생성되었습니다: {path}')
        else:
            logging.error('가이드 생성에 실패했습니다.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = PlannerGUI()
    gui.show()
    sys.exit(app.exec_())
