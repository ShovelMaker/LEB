# D:\LEB\tests\test_item_tooltip.py

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 이 import 문에서 SyntaxError가 발생하고 있었습니다.
# 파일이 깨끗하다면, pytest.ini 설정에 따라 src 폴더를 찾을 것입니다.
from src.item_tooltip import ItemListWidget

@pytest.fixture(scope="session")
def qapp_instance():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_item_addition_and_tooltip_data_storage(qapp_instance):
    item_list_widget = ItemListWidget()
    test_data = {
        'name': '강철 투구',
        'tooltip_html': '<h3>강철 투구</h3><p>방어력: +5</p><p>단단함</p>'
    }
    item_list_widget.add_item(test_data)

    assert item_list_widget.list_widget.count() == 1, "아이템이 리스트에 추가되지 않았거나, 하나 이상 추가되었습니다."
    added_item = item_list_widget.list_widget.item(0)
    assert added_item is not None, "추가된 아이템 객체를 가져올 수 없습니다."
    assert added_item.text() == test_data['name'], "아이템의 이름이 올바르게 설정되지 않았습니다."
    stored_data = added_item.data(Qt.UserRole)
    assert stored_data is not None, "아이템의 Qt.UserRole에 저장된 데이터가 없습니다."
    assert isinstance(stored_data, dict), "Qt.UserRole에 저장된 데이터가 사전(dict) 타입이 아닙니다."
    expected_tooltip_html = test_data['tooltip_html']
    assert 'tooltip_html' in stored_data, "'tooltip_html' 키가 저장된 데이터에 존재하지 않습니다."
    assert stored_data['tooltip_html'] == expected_tooltip_html, "저장된 툴팁 HTML 내용이 예상과 다릅니다."
