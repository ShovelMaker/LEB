# D:\LEB\src\item_tooltip.py

from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout
from PyQt5.QtCore import Qt

class ItemListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = QListWidget()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.list_widget)
        self.setLayout(main_layout) # 레이아웃 설정

    def add_item(self, item_data: dict):
        """
        아이템 데이터를 리스트 위젯에 추가합니다.

        Args:
            item_data (dict): 아이템 정보를 담은 딕셔너리.
                              {'name': str, 'tooltip_html': str} 형태를 기대합니다.
        """
        name = item_data.get('name', '이름 없음')
        tooltip_html = item_data.get('tooltip_html', '') # 기본값으로 빈 문자열

        list_item = QListWidgetItem(name) # 아이템 이름으로 QListWidgetItem 생성

        # 아이템에 관련된 추가 데이터(여기서는 툴팁 HTML)를 저장합니다.
        # Qt.UserRole은 사용자 정의 데이터를 저장하기 위한 표준적인 방법입니다.
        custom_data = {'tooltip_html': tooltip_html}
        list_item.setData(Qt.UserRole, custom_data)

        self.list_widget.addItem(list_item) # 리스트 위젯에 아이템 추가

    # 참고: 실제 애플리케이션에서 툴팁을 '보여주는' 기능을 구현하려면,
    # 이 위젯의 eventFilter 메소드를 오버라이드하거나,
    # QListWidget의 itemEntered 시그널 등을 활용하여
    # 저장된 tooltip_html 데이터를 가져와 화면에 표시하는 로직이 추가되어야 합니다.
    # 현재 코드는 데이터 저장까지만 구현되어 있으며, 제공된 테스트는 이 부분을 검증합니다.
