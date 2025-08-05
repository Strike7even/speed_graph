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
        self.main_table.setRowCount(6)  # 헤더 2행 + 구간1(2행) + 구간2(2행)
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
        self.main_table.setRowHeight(0, 50)  # 헤더 1행
        self.main_table.setRowHeight(1, 50)  # 헤더 2행
        for row in range(2, 6):  # 구간 데이터 행들
            self.main_table.setRowHeight(row, 30)
    
    def _setup_initial_data(self):
        """초기 데이터 설정"""
        # 첫 번째 구간 데이터 (2행 사용: Time행, Vel행)
        self._add_segment_data(2, 1)
        
        # 두 번째 구간 데이터 (2행 사용: Time행, Vel행)
        self._add_segment_data(4, 2)
    
    def _add_segment_data(self, start_row, segment_num):
        """구간 데이터 추가 (2행 사용: Time행, Vel행)"""
        # 첫 번째 행 (Time 행)
        time_row = start_row
        # 두 번째 행 (Vel 행)
        vel_row = start_row + 1
        
        # 구간 번호 (2행에 걸쳐 병합, 현재는 첫 번째 행에만 표시)
        segment_item = QTableWidgetItem(str(segment_num))
        segment_item.setTextAlignment(Qt.AlignCenter)
        self.main_table.setItem(time_row, 0, segment_item)
        
        # 빈 셀로 두 번째 행 구간 번호 셀
        empty_item = QTableWidgetItem("")
        self.main_table.setItem(vel_row, 0, empty_item)
        
        # Time 행 설정
        for col in range(1, 11):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            
            # Time 행의 색상 설정
            if col in [1, 2, 8]:  # frame_start, frame_end, acceleration (사용자 입력)
                item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
            elif col in [3]:  # distance (PC-Crash 연동)
                item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
            elif col in [4, 6]:  # avg_time, acc_time (자동 계산)
                item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
            else:  # 나머지 (빈 셀)
                pass
            
            self.main_table.setItem(time_row, col, item)
        
        # Vel 행 설정
        for col in range(1, 11):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            
            # Vel 행의 색상 설정
            if col in [5, 7]:  # avg_velocity, acc_velocity (자동 계산)
                item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
            elif col in [9, 10]:  # duration, acc_dec_type (자동 계산)
                item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
            else:  # 나머지 (빈 셀)
                pass
            
            self.main_table.setItem(vel_row, col, item)
    
    def _add_segment_row(self, row, segment_num):
        """기존 메서드 유지 (호환성)"""
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
        
        # 테이블 데이터 변경 시그널 연결
        self.main_table.itemChanged.connect(self._on_table_item_changed)
        self.fps_table.itemChanged.connect(self._on_fps_changed)
        
        # Data Bridge 시그널 연결
        if self.data_bridge:
            self.data_bridge.table_data_updated.connect(self._on_data_updated)
            self.data_bridge.error_occurred.connect(self._show_error_message)
    
    # === 버튼 이벤트 핸들러 ===
    
    def _add_segment(self):
        """구간 추가"""
        try:
            current_rows = self.main_table.rowCount()
            segment_num = (current_rows - 2) // 2 + 1  # 헤더 2행 제외, 2행씩 그룹
            
            # 새 구간을 위한 2행 추가
            self.main_table.insertRow(current_rows)
            self.main_table.insertRow(current_rows + 1)
            
            # 새 구간 데이터 설정 (2행 사용)
            self._add_segment_data(current_rows, segment_num)
            
            # 행 높이 설정
            self.main_table.setRowHeight(current_rows, 30)
            self.main_table.setRowHeight(current_rows + 1, 30)
            
            # Data Bridge의 세그먼트 데이터에도 추가
            if self.data_bridge:
                project_data = self.data_bridge.get_project_data()
                new_segment = {
                    'segment_num': segment_num,
                    'frame_start': '',
                    'frame_end': '',
                    'distance': '',
                    'avg_time': 0.0,
                    'avg_velocity': 0.0,
                    'acc_time': 0.0,
                    'acc_velocity': 0.0,
                    'acceleration': 0.0,
                    'duration': 0.0,
                    'acc_dec_type': ''
                }
                project_data['segments'].append(new_segment)
                
                # 변경사항 플래그 설정
                self.data_bridge._unsaved_changes = True
            
            self.logger.info(f"구간 {segment_num} 추가 완료")
            
        except Exception as e:
            self.logger.error(f"구간 추가 실패: {e}")
            self._show_error_message("구간 추가 오류", f"구간 추가 중 오류가 발생했습니다:\n{e}")
    
    def _remove_segment(self):
        """구간 제거"""
        try:
            current_rows = self.main_table.rowCount()
            
            # 최소 구간 수 확인 (헤더 2행 + 최소 1개 구간 2행 = 4행)
            if current_rows <= 4:
                self._show_info_message("구간 제거", "최소 1개의 구간은 유지되어야 합니다.")
                return
            
            # 마지막 구간 제거 (2행)
            segment_num = (current_rows - 2) // 2  # 현재 마지막 구간 번호
            
            # 테이블에서 마지막 2행 제거
            self.main_table.removeRow(current_rows - 1)  # Vel 행
            self.main_table.removeRow(current_rows - 2)  # Time 행
            
            # Data Bridge의 세그먼트 데이터에서도 제거
            if self.data_bridge:
                project_data = self.data_bridge.get_project_data()
                if project_data['segments']:
                    project_data['segments'].pop()  # 마지막 요소 제거
                    
                    # 변경사항 플래그 설정
                    self.data_bridge._unsaved_changes = True
            
            self.logger.info(f"구간 {segment_num} 제거 완료")
            
        except Exception as e:
            self.logger.error(f"구간 제거 실패: {e}")
            self._show_error_message("구간 제거 오류", f"구간 제거 중 오류가 발생했습니다:\n{e}")
    
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
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # 현재 테이블 데이터를 Data Bridge로 전송
            self._collect_and_send_table_data()
            
            # 파일 다이얼로그 열기
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "프로젝트 저장",
                "",
                "JSON files (*.json);;모든 파일 (*)"
            )
            
            if file_path:
                # 확장자가 없으면 .json 추가
                if not file_path.endswith('.json'):
                    file_path += '.json'
                
                # Data Bridge를 통해 저장
                if self.data_bridge:
                    success = self.data_bridge.save_project(file_path)
                    if success:
                        self._show_info_message("저장 완료", f"프로젝트가 저장되었습니다:\n{file_path}")
                        self.logger.info(f"프로젝트 저장 완료: {file_path}")
                    else:
                        self._show_error_message("저장 실패", "프로젝트 저장에 실패했습니다.")
                else:
                    self._show_error_message("저장 오류", "Data Bridge가 연결되지 않았습니다.")
            
        except Exception as e:
            self.logger.error(f"프로젝트 저장 중 오류: {e}")
            self._show_error_message("저장 오류", f"프로젝트 저장 중 오류가 발생했습니다:\n{e}")
    
    def _load_project(self):
        """프로젝트 불러오기"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            
            # 저장되지 않은 변경사항 확인
            if self.data_bridge and self.data_bridge.has_unsaved_changes():
                reply = QMessageBox.question(
                    self,
                    "저장 확인",
                    "저장하지 않은 변경사항이 있습니다.\n계속하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # 파일 다이얼로그 열기
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "프로젝트 불러오기",
                "",
                "JSON files (*.json);;모든 파일 (*)"
            )
            
            if file_path:
                if self.data_bridge:
                    success = self.data_bridge.load_project(file_path)
                    if success:
                        # 테이블에 로드된 데이터 표시
                        self._refresh_table_from_data()
                        self._show_info_message("불러오기 완료", f"프로젝트를 불러왔습니다:\n{file_path}")
                        self.logger.info(f"프로젝트 불러오기 완료: {file_path}")
                    else:
                        self._show_error_message("불러오기 실패", "프로젝트 불러오기에 실패했습니다.")
                else:
                    self._show_error_message("불러오기 오류", "Data Bridge가 연결되지 않았습니다.")
            
        except Exception as e:
            self.logger.error(f"프로젝트 불러오기 중 오류: {e}")
            self._show_error_message("불러오기 오류", f"프로젝트 불러오기 중 오류가 발생했습니다:\n{e}")
    
    def _open_settings(self):
        """설정 열기"""
        # TODO: Phase 5에서 설정 다이얼로그 구현
        self.logger.info("설정 열기 요청")
    
    # === 데이터 업데이트 핸들러 ===
    
    def _on_table_item_changed(self, item):
        """테이블 아이템 변경 처리"""
        try:
            row = item.row()
            col = item.column()
            
            # 헤더 행은 무시
            if row < 2:
                return
            
            # 사용자 입력 가능한 셀만 처리
            if col in [1, 2, 3, 8]:  # frame_start, frame_end, distance, acceleration
                self.logger.debug(f"테이블 셀 변경: ({row}, {col}) = {item.text()}")
                
                # END 프레임 변경 시 다음 구간 START 프레임 자동 업데이트
                if col == 2:  # frame_end 변경
                    self._auto_fill_next_segment_start(row, item.text())
                
                # 실시간으로 Data Bridge에 업데이트
                self._collect_and_send_table_data()
        
        except Exception as e:
            self.logger.error(f"테이블 아이템 변경 처리 실패: {e}")
    
    def _auto_fill_next_segment_start(self, current_row, end_frame_value):
        """다음 구간의 START 프레임 자동 입력"""
        try:
            if not end_frame_value or not end_frame_value.strip():
                return
            
            # 현재 구간이 어느 구간인지 파악 (2행씩 그룹)
            # 구간1: 행 2,3 / 구간2: 행 4,5 / 구간3: 행 6,7 ...
            current_segment = (current_row - 2) // 2 + 1
            next_segment_time_row = current_row + 2  # 다음 구간의 Time 행
            
            # 다음 구간이 존재하는지 확인
            if next_segment_time_row < self.main_table.rowCount():
                # 다음 구간의 START 프레임 (col 1) 자동 입력
                next_start_item = self.main_table.item(next_segment_time_row, 1)
                if next_start_item:
                    # 시그널 연결을 일시적으로 해제하여 무한 루프 방지
                    self.main_table.itemChanged.disconnect(self._on_table_item_changed)
                    next_start_item.setText(end_frame_value)
                    self.main_table.itemChanged.connect(self._on_table_item_changed)
                    
                    self.logger.debug(f"구간 {current_segment + 1} START 프레임 자동 입력: {end_frame_value}")
        
        except Exception as e:
            self.logger.error(f"프레임 자동 입력 실패: {e}")
            # 시그널 연결 복구
            self.main_table.itemChanged.connect(self._on_table_item_changed)
    
    def _on_fps_changed(self, item):
        """FPS 값 변경 처리"""
        try:
            if item.row() == 0 and item.column() == 1:
                self.logger.debug(f"FPS 값 변경: {item.text()}")
                
                # 실시간으로 Data Bridge에 업데이트
                self._collect_and_send_table_data()
        
        except Exception as e:
            self.logger.error(f"FPS 변경 처리 실패: {e}")
    
    def _on_data_updated(self, data):
        """데이터 업데이트 처리"""
        try:
            self.logger.debug("테이블 데이터 업데이트 수신")
            
            # 데이터가 dict 형태로 전달되는지 확인
            if isinstance(data, dict) and 'segments' in data:
                # Data Bridge의 세그먼트 데이터로 테이블 새로고침
                if self.data_bridge:
                    # 기존 데이터 업데이트
                    self.data_bridge._project_data['segments'] = data['segments']
                    # 테이블 새로고침
                    self._refresh_table_from_data()
            
        except Exception as e:
            self.logger.error(f"데이터 업데이트 처리 실패: {e}")
            self._show_error_message("데이터 업데이트 오류", f"테이블 업데이트 중 오류가 발생했습니다: {e}")
    
    # === 데이터 수집 및 새로고침 메서드 ===
    
    def _collect_and_send_table_data(self):
        """테이블 데이터 수집 후 Data Bridge로 전송"""
        try:
            segments_data = []
            
            # 메인 테이블에서 구간별 데이터 처리 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                time_row = row
                vel_row = row + 1
                
                # 각 구간의 데이터 추출
                segment_data = {}
                segment_data['segment_num'] = self._get_cell_value(time_row, 0)
                segment_data['frame_start'] = self._get_cell_value(time_row, 1)
                segment_data['frame_end'] = self._get_cell_value(time_row, 2)
                segment_data['distance'] = self._get_cell_value(time_row, 3)
                segment_data['avg_time'] = self._get_cell_value(time_row, 4)
                segment_data['avg_velocity'] = self._get_cell_value(vel_row, 5) if vel_row < self.main_table.rowCount() else ""
                segment_data['acc_time'] = self._get_cell_value(time_row, 6)
                segment_data['acc_velocity'] = self._get_cell_value(vel_row, 7) if vel_row < self.main_table.rowCount() else ""
                segment_data['acceleration'] = self._get_cell_value(time_row, 8)
                segment_data['duration'] = self._get_cell_value(vel_row, 9) if vel_row < self.main_table.rowCount() else ""
                segment_data['acc_dec_type'] = self._get_cell_value(vel_row, 10) if vel_row < self.main_table.rowCount() else ""
                
                segments_data.append(segment_data)
            
            # FPS 값 추출
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            
            # Data Bridge로 전송
            if self.data_bridge:
                table_data = {
                    'segments': segments_data,
                    'settings': {
                        'fps': float(fps_value) if fps_value else 30.0
                    }
                }
                self.data_bridge.update_from_table(table_data)
                self.logger.debug("테이블 데이터 전송 완료")
            
        except Exception as e:
            self.logger.error(f"테이블 데이터 수집 실패: {e}")
    
    def _get_cell_value(self, row, col):
        """테이블 셀 값 가져오기"""
        item = self.main_table.item(row, col)
        return item.text().strip() if item else ""
    
    def _get_cell_value_from_table(self, table, row, col):
        """특정 테이블에서 셀 값 가져오기"""
        item = table.item(row, col)
        return item.text().strip() if item else ""
    
    def _refresh_table_from_data(self):
        """Data Bridge의 데이터로 테이블 새로고침"""
        try:
            if not self.data_bridge:
                return
            
            project_data = self.data_bridge.get_project_data()
            segments = project_data.get('segments', [])
            settings = project_data.get('settings', {})
            
            # 기존 데이터 행 제거 (헤더 제외)
            while self.main_table.rowCount() > 2:
                self.main_table.removeRow(2)
            
            # 세그먼트 데이터 행 추가
            for i, segment in enumerate(segments):
                row = i + 2  # 헤더 다음부터
                self.main_table.insertRow(row)
                
                # 각 셀에 데이터 설정
                self._set_cell_value(row, 0, str(segment.get('segment_num', i + 1)))
                self._set_cell_value(row, 1, str(segment.get('frame_start', '')))
                self._set_cell_value(row, 2, str(segment.get('frame_end', '')))
                self._set_cell_value(row, 3, str(segment.get('distance', '')))
                self._set_cell_value(row, 4, str(segment.get('avg_time', '')))
                self._set_cell_value(row, 5, str(segment.get('avg_velocity', '')))
                self._set_cell_value(row, 6, str(segment.get('acc_time', '')))
                self._set_cell_value(row, 7, str(segment.get('acc_velocity', '')))
                self._set_cell_value(row, 8, str(segment.get('acceleration', '')))
                self._set_cell_value(row, 9, str(segment.get('duration', '')))
                self._set_cell_value(row, 10, str(segment.get('acc_dec_type', '')))
                
                # 행 높이 설정
                self.main_table.setRowHeight(row, 30)
            
            # FPS 값 설정
            fps_value = settings.get('fps', 30.0)
            fps_item = self.fps_table.item(0, 1)
            if fps_item:
                fps_item.setText(str(fps_value))
            
            self.logger.debug("테이블 새로고침 완료")
            
        except Exception as e:
            self.logger.error(f"테이블 새로고침 실패: {e}")
    
    def _set_cell_value(self, row, col, value):
        """테이블 셀 값 설정"""
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignCenter)
        
        # 색상 설정
        if col in [1, 2, 8, 9]:  # 사용자 입력
            item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
        elif col in [3]:  # PC-Crash 연동
            item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
        else:  # 자동 계산
            item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
        
        self.main_table.setItem(row, col, item)
    
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