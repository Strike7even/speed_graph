import sys
from PyQt5.QtWidgets import QApplication
from velocity_table import TableWindow
from velocity_graph import GraphWindow
from data_bridge import DataBridge

def main():
    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 데이터 브릿지 생성
    data_bridge = DataBridge()
    
    # 창 생성
    table_window = TableWindow(data_bridge)
    graph_window = GraphWindow(data_bridge)
    
    # 데이터 브릿지에 창 연결
    data_bridge.set_table_window(table_window)
    data_bridge.set_graph_window(graph_window)
    
    # 창 표시
    table_window.show()
    graph_window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()