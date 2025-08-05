"""
VelocityOptimizer - 메인 컨트롤러
시스템의 진입점 및 전체 컴포넌트 관리
"""

import sys
import logging
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal

from data_bridge import DataBridge
from table_window import TableWindow
from graph_window import GraphWindow

class VelocityOptimizer(QObject):
    """메인 컨트롤러 클래스"""
    
    # 시그널 정의
    shutdown_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 컴포넌트 초기화
        self.data_bridge = None
        self.table_window = None
        self.graph_window = None
        
        self._initialize_components()
        self._connect_signals()
        
        self.logger.info("VelocityOptimizer 초기화 완료")
    
    def _initialize_components(self):
        """모든 컴포넌트 초기화"""
        try:
            # Data Bridge 생성
            self.data_bridge = DataBridge()
            
            # 윈도우 생성
            self.table_window = TableWindow(self.data_bridge)
            self.graph_window = GraphWindow(self.data_bridge)
            
            # Data Bridge에 윈도우 연결
            self.data_bridge.set_windows(self.table_window, self.graph_window)
            
            self.logger.info("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 실패: {e}")
            self._show_error_message("초기화 오류", f"프로그램 초기화 중 오류가 발생했습니다:\n{e}")
            sys.exit(1)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 윈도우 종료 시그널 연결
        self.table_window.window_closing.connect(self._on_window_closing)
        self.graph_window.window_closing.connect(self._on_window_closing)
        
        # 자체 종료 시그널 연결
        self.shutdown_requested.connect(self._shutdown)
    
    def show(self):
        """윈도우 표시"""
        try:
            # 두 윈도우를 나란히 배치
            self.table_window.show()
            self.graph_window.show()
            
            # 초기 위치 설정 (좌우 배치)
            table_geometry = self.table_window.geometry()
            self.graph_window.move(
                table_geometry.x() + table_geometry.width() + 10,
                table_geometry.y()
            )
            
            self.logger.info("윈도우 표시 완료")
            
        except Exception as e:
            self.logger.error(f"윈도우 표시 실패: {e}")
            self._show_error_message("표시 오류", f"윈도우 표시 중 오류가 발생했습니다:\n{e}")
    
    def _on_window_closing(self):
        """윈도우 종료 이벤트 처리"""
        self.logger.info("윈도우 종료 요청 수신")
        
        # 데이터 저장 확인
        if self._check_unsaved_changes():
            reply = QMessageBox.question(
                None,
                "저장 확인",
                "저장하지 않은 변경사항이 있습니다.\n종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # 종료 처리
        self.shutdown_requested.emit()
    
    def _check_unsaved_changes(self):
        """저장되지 않은 변경사항 확인"""
        # TODO: 실제 구현에서는 데이터 변경 상태를 확인
        return self.data_bridge.has_unsaved_changes() if self.data_bridge else False
    
    def _shutdown(self):
        """애플리케이션 종료"""
        try:
            self.logger.info("애플리케이션 종료 시작")
            
            # 윈도우 닫기
            if self.table_window:
                self.table_window.close()
            if self.graph_window:
                self.graph_window.close()
            
            # 리소스 정리
            if self.data_bridge:
                self.data_bridge.cleanup()
            
            # 애플리케이션 종료
            QApplication.quit()
            
            self.logger.info("애플리케이션 종료 완료")
            
        except Exception as e:
            self.logger.error(f"종료 처리 중 오류: {e}")
    
    def _show_error_message(self, title, message):
        """에러 메시지 표시"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
    
    def get_data_bridge(self):
        """Data Bridge 참조 반환"""
        return self.data_bridge
    
    def get_table_window(self):
        """Table Window 참조 반환"""
        return self.table_window
    
    def get_graph_window(self):
        """Graph Window 참조 반환"""
        return self.graph_window