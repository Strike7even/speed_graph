"""
TableWindow - 테이블 윈도우
데이터 입력 및 관리 인터페이스
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from utils.constants import (
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    USER_INPUT_COLOR, AUTO_CALCULATION_COLOR, PC_CRASH_INTEGRATION_COLOR
)

class TableWindow(QMainWindow):
    """테이블 윈도우 클래스"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    data_changed = pyqtSignal(dict)
    
    def __init__(self, data_bridge):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.data_bridge = data_bridge
        
        # UI 초기화
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("TableWindow 초기화 완료")
    
    def _setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("속도 최적화 프로그램 - 데이터 테이블")
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 메인 테이블 생성
        self._create_main_table()
        main_layout.addWidget(self.main_table)
        
        # 하단 레이아웃 (FPS 테이블 + 정보 테이블)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # FPS 테이블 생성
        self._create_fps_table()
        bottom_layout.addWidget(self.fps_table)
        
        # 스트레치 추가
        bottom_layout.addStretch(1)
        
        # 정보 테이블 생성
        self._create_info_table()
        bottom_layout.addWidget(self.info_table)
        
        main_layout.addLayout(bottom_layout)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 구간 추가/삭제 버튼
        self.add_button = QPushButton("+")
        self.remove_button = QPushButton("-")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        
        # PC-Crash 연동 버튼들
        self.fetch_distance_button = QPushButton("거리정보 가져오기")
        self.send_simulation_button = QPushButton("시뮬레이션 연동")
        button_layout.addWidget(self.fetch_distance_button)
        button_layout.addWidget(self.send_simulation_button)
        
        # 파일 버튼들
        self.save_button = QPushButton("저장")
        self.load_button = QPushButton("불러오기")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        
        # 설정 버튼
        self.settings_button = QPushButton("설정")
        button_layout.addWidget(self.settings_button)
        
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
    
    def _create_main_table(self):
        """메인 테이블 생성"""
        self.main_table = QTableWidget()
        
        # 기본 테이블 설정
        self.main_table.setRowCount(4)  # 헤더 2행 + 데이터 2행
        self.main_table.setColumnCount(11)
        
        # 헤더 숨기기
        self.main_table.verticalHeader().setVisible(False)
        self.main_table.horizontalHeader().setVisible(False)
        
        # 테이블 구조 설정
        self._setup_table_structure()
        
        # 초기 데이터 설정
        self._setup_initial_data()
    
    def _setup_table_structure(self):
        """테이블 구조 설정 (논문과 동일)"""
        # 첫 번째 행 (상위 헤더)
        headers_row1 = [
            "구간", "START", "END", "거리",
            "구간별 평균속도", "", 
            "가속도 적용", "",
            "Acc", "Duration", "Acc/Dec"
        ]
        
        # 두 번째 행 (하위 헤더)
        headers_row2 = [
            "", "", "", "",
            "Time", "Vel",
            "Time", "Vel", 
            "", "", ""
        ]
        
        # 헤더 설정
        for col, header in enumerate(headers_row1):
            item = QTableWidgetItem(header)
            item.setTextAlignment(Qt.AlignCenter)
            self.main_table.setItem(0, col, item)
        
        for col, header in enumerate(headers_row2):
            item = QTableWidgetItem(header)
            item.setTextAlignment(Qt.AlignCenter)
            self.main_table.setItem(1, col, item)
        
        # 셀 병합 (추후 구현)
        # TODO: Phase 2에서 상세 구현
        
        # 열 너비 설정
        for col in range(11):
            self.main_table.setColumnWidth(col, 100)
        
        # 행 높이 설정
        self.main_table.setRowHeight(0, 50)
        self.main_table.setRowHeight(1, 50)
        for row in range(2, 4):
            self.main_table.setRowHeight(row, 30)
    
    def _setup_initial_data(self):
        """초기 데이터 설정"""
        # 첫 번째 구간 데이터
        self._add_segment_row(2, 1)
        
        # 두 번째 구간 데이터
        self._add_segment_row(3, 2)
    
    def _add_segment_row(self, row, segment_num):
        """구간 행 추가"""
        # 구간 번호
        item = QTableWidgetItem(str(segment_num))
        item.setTextAlignment(Qt.AlignCenter)
        self.main_table.setItem(row, 0, item)
        
        # 나머지 셀 초기화
        for col in range(1, 11):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            
            # 색상 설정
            if col in [1, 2, 8, 9]:  # 사용자 입력
                item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
            elif col in [3]:  # PC-Crash 연동
                item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
            else:  # 자동 계산
                item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
            
            self.main_table.setItem(row, col, item)
    
    def _create_fps_table(self):
        """FPS 테이블 생성"""
        self.fps_table = QTableWidget()
        self.fps_table.setRowCount(1)
        self.fps_table.setColumnCount(2)
        self.fps_table.setFixedHeight(35)
        self.fps_table.setFixedWidth(202)
        
        # 헤더 숨기기
        self.fps_table.verticalHeader().setVisible(False)
        self.fps_table.horizontalHeader().setVisible(False)
        
        # FPS 레이블
        fps_label = QTableWidgetItem("FPS")
        fps_label.setTextAlignment(Qt.AlignCenter)
        self.fps_table.setItem(0, 0, fps_label)
        
        # FPS 입력 셀
        fps_input = QTableWidgetItem("")
        fps_input.setTextAlignment(Qt.AlignCenter)
        fps_input.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
        self.fps_table.setItem(0, 1, fps_input)
        
        # 열 너비 설정
        self.fps_table.setColumnWidth(0, 100)
        self.fps_table.setColumnWidth(1, 100)
        self.fps_table.setRowHeight(0, 35)
    
    def _create_info_table(self):
        """정보 테이블 생성"""
        self.info_table = QTableWidget()
        self.info_table.setRowCount(1)
        self.info_table.setColumnCount(3)
        self.info_table.setFixedHeight(35)
        self.info_table.setFixedWidth(302)
        
        # 헤더 숨기기
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setVisible(False)
        
        # 정보 항목들
        info_items = [
            ("사용자 입력", USER_INPUT_COLOR),
            ("자동계산", AUTO_CALCULATION_COLOR),
            ("PCC 연동", PC_CRASH_INTEGRATION_COLOR)
        ]
        
        for col, (text, color) in enumerate(info_items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QBrush(QColor(color)))
            self.info_table.setItem(0, col, item)
        
        # 열 너비 설정
        for col in range(3):
            self.info_table.setColumnWidth(col, 100)
        self.info_table.setRowHeight(0, 35)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 버튼 시그널 연결
        self.add_button.clicked.connect(self._add_segment)
        self.remove_button.clicked.connect(self._remove_segment)
        
        self.fetch_distance_button.clicked.connect(self._fetch_distance_data)
        self.send_simulation_button.clicked.connect(self._send_simulation_data)
        
        self.save_button.clicked.connect(self._save_project)
        self.load_button.clicked.connect(self._load_project)
        self.settings_button.clicked.connect(self._open_settings)
        
        # Data Bridge 시그널 연결
        if self.data_bridge:
            self.data_bridge.table_data_updated.connect(self._on_data_updated)
            self.data_bridge.error_occurred.connect(self._show_error_message)
    
    # === 버튼 이벤트 핸들러 ===
    
    def _add_segment(self):
        """구간 추가"""
        # TODO: Phase 2에서 구현
        self.logger.info("구간 추가 요청")
    
    def _remove_segment(self):
        """구간 제거"""
        # TODO: Phase 2에서 구현
        self.logger.info("구간 제거 요청")
    
    def _fetch_distance_data(self):
        """거리 데이터 가져오기"""
        if self.data_bridge:
            success = self.data_bridge.fetch_distance_data()
            if success:
                self._show_info_message("PC-Crash 연동", "거리 데이터를 가져왔습니다.")
            else:
                self._show_error_message("PC-Crash 연동 오류", "거리 데이터를 가져오는데 실패했습니다.")
    
    def _send_simulation_data(self):
        """시뮬레이션 데이터 전송"""
        if self.data_bridge:
            success = self.data_bridge.send_simulation_data()
            if success:
                self._show_info_message("PC-Crash 연동", "시뮬레이션 데이터를 전송했습니다.")
            else:
                self._show_error_message("PC-Crash 연동 오류", "시뮬레이션 데이터 전송에 실패했습니다.")
    
    def _save_project(self):
        """프로젝트 저장"""
        # TODO: Phase 2에서 파일 다이얼로그 구현
        self.logger.info("프로젝트 저장 요청")
    
    def _load_project(self):
        """프로젝트 불러오기"""
        # TODO: Phase 2에서 파일 다이얼로그 구현
        self.logger.info("프로젝트 불러오기 요청")
    
    def _open_settings(self):
        """설정 열기"""
        # TODO: Phase 5에서 설정 다이얼로그 구현
        self.logger.info("설정 열기 요청")
    
    # === 데이터 업데이트 핸들러 ===
    
    def _on_data_updated(self, data):
        """데이터 업데이트 처리"""
        # TODO: Phase 4에서 구현
        self.logger.debug("테이블 데이터 업데이트 수신")
    
    # === 유틸리티 메서드 ===
    
    def _show_error_message(self, title, message):
        """에러 메시지 표시"""
        QMessageBox.critical(self, title, message)
    
    def _show_info_message(self, title, message):
        """정보 메시지 표시"""
        QMessageBox.information(self, title, message)
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        self.window_closing.emit()
        event.accept()