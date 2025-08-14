"""
TableWindow - 테이블 윈도우
데이터 입력 및 관리 인터페이스
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from utils.constants import (
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    USER_INPUT_COLOR, AUTO_CALCULATION_COLOR, PC_CRASH_INTEGRATION_COLOR,
    ACCELERATION_VALID_CELL_COLOR, ACCELERATION_INVALID_CELL_COLOR, ACCELERATION_UNIFORM_CELL_COLOR,
    DEFAULT_UNIFORM_MOTION_THRESHOLD
)

class TableWindow(QMainWindow):
    """테이블 윈도우 클래스"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    data_changed = pyqtSignal(dict)
    
    def __init__(self, data_bridge):
        super().__init__()
        self.data_bridge = data_bridge
        
        # UI 초기화
        self._setup_ui()
        self._connect_signals()
    
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
        
        # 프리셋 버튼들
        self.preset1_button = QPushButton("프리셋1")
        self.preset2_button = QPushButton("프리셋2")
        button_layout.addWidget(self.preset1_button)
        button_layout.addWidget(self.preset2_button)
        
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
    
    def _add_segment_data(self, start_row, segment_num, auto_fill_start_frame=None):
        """구간 데이터 추가 (2행 사용: Time행, Vel행)
        
        Args:
            start_row: 시작 행 번호
            segment_num: 구간 번호
            auto_fill_start_frame: 자동으로 채울 START 프레임 값 (이전 구간의 END 프레임)
        """
        # 구간 시작 상태 행 (병합된 셀들이 위치하는 행)
        segment_start_row = start_row
        # 구간 끝 상태 행 (분리된 셀들의 끝 데이터가 위치하는 행)
        segment_end_row = start_row + 1
        
        # 병합 대상 열 (0, 1, 2, 3, 4, 5, 8, 9, 10) - Time과 Vel도 병합 추가
        merge_columns = [0, 1, 2, 3, 4, 5, 8, 9, 10]
        
        for col in range(11):
            if col in merge_columns:
                # 병합 대상 열: 구간 시작 행에만 값 설정하고 rowspan=2 적용
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                
                # 구간 번호
                if col == 0:
                    item.setText(str(segment_num))
                # START 프레임 자동 입력
                elif col == 1 and auto_fill_start_frame:
                    item.setText(str(auto_fill_start_frame))
                
                # 색상 설정
                if col in [1, 2, 8]:  # frame_start, frame_end, acceleration (사용자 입력)
                    item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
                elif col == 3:  # distance (PC-Crash 연동)
                    item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
                elif col in [4, 5, 9, 10]:  # time, velocity, duration, acc_dec_type (자동 계산)
                    item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                
                self.main_table.setItem(segment_start_row, col, item)
                # setSpan으로 셀 병합 (row, col, rowspan, colspan)
                self.main_table.setSpan(segment_start_row, col, 2, 1)
                
            else:
                # 병합하지 않는 열 (6, 7): 각 행에 개별 값 설정
                # 구간 시작 행 (시작 상태 데이터)
                start_item = QTableWidgetItem("")
                start_item.setTextAlignment(Qt.AlignCenter)
                
                # 6열: 자동 계산 색상 (가속도 적용 시간)
                # 7열: 자동 계산 색상 (최적화 속도)
                if col == 6:  # acc_time은 자동 계산
                    start_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                    start_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                
                self.main_table.setItem(segment_start_row, col, start_item)
                
                # 구간 끝 행 (끝 상태 데이터)
                end_item = QTableWidgetItem("")
                end_item.setTextAlignment(Qt.AlignCenter)
                
                # 6열: 자동 계산 색상 (가속도 적용 시간)
                # 7열: 자동 계산 색상 (최적화 속도)
                if col == 6:  # acc_time은 자동 계산
                    end_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                    end_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                
                self.main_table.setItem(segment_end_row, col, end_item)
    
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
        
        # 프리셋 버튼 시그널 연결
        self.preset1_button.clicked.connect(self._load_preset1)
        self.preset2_button.clicked.connect(self._load_preset2)
        
        # 테이블 데이터 변경 시그널 연결
        self.main_table.itemChanged.connect(self._on_table_item_changed)
        self.fps_table.itemChanged.connect(self._on_fps_changed)
        
        # Data Bridge 시그널 연결
        if self.data_bridge:
            self.data_bridge.table_data_updated.connect(self._on_data_updated)
            self.data_bridge.graph_data_updated.connect(self._on_graph_data_updated)  # 그래프 데이터 시그널 추가
            self.data_bridge.error_occurred.connect(self._show_error_message)
    
    # === 버튼 이벤트 핸들러 ===
    
    def _add_segment(self):
        """구간 추가"""
        try:
            current_rows = self.main_table.rowCount()
            segment_num = (current_rows - 2) // 2 + 1  # 헤더 2행 제외, 2행씩 그룹
            
            # 이전 구간의 END 프레임 값 가져오기
            auto_fill_start = None
            if current_rows > 2:  # 이전 구간이 존재하는 경우
                prev_segment_start_row = current_rows - 2  # 이전 구간의 시작 행
                end_frame_item = self.main_table.item(prev_segment_start_row, 2)  # END 프레임 (2번 열)
                if end_frame_item and end_frame_item.text().strip():
                    auto_fill_start = end_frame_item.text().strip()
            
            # 새 구간을 위한 2행 추가
            self.main_table.insertRow(current_rows)
            self.main_table.insertRow(current_rows + 1)
            
            # 새 구간 데이터 설정 (2행 사용, START 프레임 자동 입력)
            self._add_segment_data(current_rows, segment_num, auto_fill_start)
            
            # 행 높이 설정
            self.main_table.setRowHeight(current_rows, 30)
            self.main_table.setRowHeight(current_rows + 1, 30)
            
            # Data Bridge의 세그먼트 데이터에도 추가
            if self.data_bridge:
                project_data = self.data_bridge.get_project_data()
                new_segment = {
                    'segment_num': segment_num,
                    'frame_start': auto_fill_start if auto_fill_start else '',
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
            
            # 구간 추가 후 그래프 업데이트를 위해 데이터 전송
            self._collect_and_send_table_data()
            
            
        except Exception as e:
            pass
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
            
            # 구간 삭제 후 그래프 업데이트를 위해 데이터 전송
            self._collect_and_send_table_data()
            

            
        except Exception as e:
            pass
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

                    else:
                        self._show_error_message("저장 실패", "프로젝트 저장에 실패했습니다.")
                else:
                    self._show_error_message("저장 오류", "Data Bridge가 연결되지 않았습니다.")
            
        except Exception as e:
            pass
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

                    else:
                        self._show_error_message("불러오기 실패", "프로젝트 불러오기에 실패했습니다.")
                else:
                    self._show_error_message("불러오기 오류", "Data Bridge가 연결되지 않았습니다.")
            
        except Exception as e:
            pass
            self._show_error_message("불러오기 오류", f"프로젝트 불러오기 중 오류가 발생했습니다:\n{e}")
    
    def _open_settings(self):
        """설정 열기"""
        # TODO: Phase 5에서 설정 다이얼로그 구현

    
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

                
                # END 프레임 변경 시 다음 구간 START 프레임 자동 업데이트
                if col == 2:  # frame_end 변경
                    self._auto_fill_next_segment_start(row, item.text())
                
                # 자동 계산 실행
                self._check_and_calculate_auto_values()
                
                # 8열(가속도) 값이 변경된 경우 10열 색상 업데이트
                if col == 8:
                    # 짝수 행만 처리 (구간 시작 행)
                    if row % 2 == 0:
                        self._update_acc_dec_color(row)
                
                # 1~6열 변경시에만 Data Bridge 업데이트 (7~10열은 그래프에서 계산됨)
                if col < 6:  # 0~5 인덱스 = 1~6열
                    self._collect_and_send_table_data()
        
        except Exception as e:
            pass
    
    def _auto_fill_next_segment_start(self, current_row, end_frame_value):
        """다음 구간의 START 프레임 자동 입력"""
        try:
            if not end_frame_value or not end_frame_value.strip():
                return
            
            # 현재 구간이 어느 구간인지 파악 (2행씩 그룹)
            # 구간1: 행 2,3 / 구간2: 행 4,5 / 구간3: 행 6,7 ...
            current_segment = (current_row - 2) // 2 + 1
            next_segment_start_row = current_row + 2  # 다음 구간의 시작 행
            
            # 다음 구간이 존재하는지 확인
            if next_segment_start_row < self.main_table.rowCount():
                # 다음 구간의 START 프레임 (col 1) 자동 입력
                next_start_item = self.main_table.item(next_segment_start_row, 1)
                if next_start_item:
                    # 시그널 연결을 일시적으로 해제하여 무한 루프 방지
                    self.main_table.itemChanged.disconnect(self._on_table_item_changed)
                    next_start_item.setText(end_frame_value)
                    self.main_table.itemChanged.connect(self._on_table_item_changed)
                    

        
        except Exception as e:
            pass
            # 시그널 연결 복구
            self.main_table.itemChanged.connect(self._on_table_item_changed)
    
    def _on_fps_changed(self, item):
        """FPS 값 변경 처리"""
        try:
            if item.row() == 0 and item.column() == 1:

                
                # 자동 계산 실행
                self._check_and_calculate_auto_values()
                
                # 실시간으로 Data Bridge에 업데이트
                self._collect_and_send_table_data()
        
        except Exception as e:
            pass
    
    def _on_data_updated(self, data):
        """데이터 업데이트 처리"""
        try:
            
            # 데이터가 dict 형태로 전달되는지 확인
            if isinstance(data, dict):
                # 최적화 그래프 데이터가 포함된 경우 7열 업데이트
                if 'optimization_velocity' in data:
                    self._update_optimization_velocity_column(data['optimization_velocity'])
                
                # 세그먼트 데이터 업데이트
                if 'segments' in data:
                    # graph_updated 플래그 확인 - 그래프에서 온 업데이트인 경우
                    if data.get('graph_updated', False):
                        # 7~10열만 업데이트 (전체 새로고침 하지 않음)
                        if self.data_bridge:
                            # segments 데이터 업데이트 (메모리상)
                            self.data_bridge._project_data['segments'] = data['segments']
                            # 7~10열만 테이블에 반영
                            self._update_columns_7_to_10_only(data['segments'])
                    else:
                        # 일반 업데이트 (1-6열 수정, 파일 로드, 구간 추가/삭제)
                        if self.data_bridge:
                            # 기존 데이터 업데이트
                            self.data_bridge._project_data['segments'] = data['segments']
                            # 테이블 새로고침
                            self._refresh_table_from_data()
            
        except Exception as e:
            pass
            self._show_error_message("데이터 업데이트 오류", f"테이블 업데이트 중 오류가 발생했습니다: {e}")
    
    def _on_graph_data_updated(self, graph_data):
        """그래프 데이터 업데이트 처리 (초기 생성 시 7, 8, 9, 10열 업데이트용)"""
        try:

            
            # 최적화 그래프 데이터가 있으면 7열 업데이트
            if 'optimization_velocity' in graph_data:

                self._update_optimization_velocity_column(graph_data['optimization_velocity'])
            
            # 8, 9, 10열 자동 계산 실행 (기존 자동 계산 로직 활용)

            self._calculate_acc_time_values()  # 6열 가속도 시간
            
            # DataBridge에서 계산된 segments 데이터 가져와서 8, 9, 10열 업데이트
            if self.data_bridge:
                project_data = self.data_bridge.get_project_data()
                segments = project_data.get('segments', [])

                self._update_calculated_columns_from_segments(segments)
            
        except Exception as e:
            pass
    
    def _update_calculated_columns_from_segments(self, segments):
        """DataBridge segments 데이터로부터 8, 9, 10열 업데이트"""
        try:

            
            # 시그널 연결 일시 해제 (무한 루프 방지)
            try:
                self.main_table.itemChanged.disconnect(self._on_table_item_changed)
            except TypeError:
                pass
            
            # 각 구간별로 처리
            for i, segment in enumerate(segments):
                row = 2 + (i * 2)  # 구간 시작 행 계산
                
                if row >= self.main_table.rowCount():
                    break
                




                
                # 8열: 가속도 (acceleration)
                acceleration = segment.get('acceleration', None)

                
                # 계산된 가속도가 있는 경우 (빈 문자열 제외, 0.0 포함)
                if acceleration is not None and acceleration != "":
                    try:
                        # 문자열이면 float으로 변환
                        if isinstance(acceleration, str):
                            acceleration = float(acceleration)
                        
                        acc_item = self.main_table.item(row, 8)
                        if acc_item:
                            acc_item.setText(f"{acceleration:.2f}")

                    except (ValueError, TypeError) as e:
                        pass
                else:
                    pass
                
                # 9열: 지속시간 (duration)
                duration = segment.get('duration', None)
                if duration is not None:  # 계산된 지속시간이 있는 경우 (0 포함, 하지만 실제로는 0이면 안됨)
                    duration_item = self.main_table.item(row, 9)
                    if duration_item:
                        duration_item.setText(f"{duration:.3f}")

                
                # 10열: 가속도 유형 및 색상 (acc_dec_type)
                acc_dec_type = segment.get('acc_dec_type', '')
                if acc_dec_type:  # 가속도 유형이 있는 경우만
                    acc_dec_item = self.main_table.item(row, 10)
                    if acc_dec_item:
                        acc_dec_item.setText(acc_dec_type)
                        
                        # 색상 설정
                        if "Valid" in acc_dec_type:
                            color = ACCELERATION_VALID_CELL_COLOR
                        elif "Invalid" in acc_dec_type:
                            color = ACCELERATION_INVALID_CELL_COLOR
                        elif "Uniform" in acc_dec_type:
                            color = ACCELERATION_UNIFORM_CELL_COLOR
                        else:
                            color = AUTO_CALCULATION_COLOR
                        
                        acc_dec_item.setBackground(QBrush(QColor(color)))

            
            # 시그널 재연결
            self.main_table.itemChanged.connect(self._on_table_item_changed)
            

            
        except Exception as e:
            pass
            # 시그널 재연결 (에러 시에도)
            try:
                self.main_table.itemChanged.connect(self._on_table_item_changed)
            except:
                pass
    
    # === 자동 계산 메서드 ===
    
    def _calculate_time_values(self):
        """4열 시간 값 자동 계산 - 병합된 셀에 구간 종료 시간 표시"""
        try:
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            if not fps_value:
                return
            
            fps = float(fps_value)
            
            # 각 구간별로 계산 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                segment_index = (row - 2) // 2
                segment_start_row = row  # 구간 시작 행
                
                # 프레임 정보 가져오기 (병합된 셀에서)
                start_frame = self._get_cell_value(segment_start_row, 1)
                end_frame = self._get_cell_value(segment_start_row, 2)
                
                if start_frame and end_frame:
                    try:
                        start_f = float(start_frame)
                        end_f = float(end_frame)
                        
                        # 구간 시간 계산 (프레임 차이 / FPS)
                        segment_time = (end_f - start_f) / fps
                        
                        # 누적 시간 계산
                        if segment_index == 0:
                            # 1구간은 0부터 시작
                            time_cumulative = 0.000
                        else:
                            # 이전 구간의 종료 시간 가져오기
                            prev_segment_start_row = row - 2
                            prev_time_str = self._get_cell_value(prev_segment_start_row, 4)
                            if prev_time_str:
                                # 이전 구간의 종료 시간을 파싱
                                time_cumulative = float(prev_time_str)
                            else:
                                time_cumulative = 0.0
                        
                        # 구간 종료 시간 계산
                        time_end = time_cumulative + segment_time
                        
                        # 병합된 셀에 구간 종료 시간 설정 (소수점 셋째자리까지)
                        time_item = self.main_table.item(segment_start_row, 4)
                        if time_item:
                            time_item.setText(f"{time_end:.3f}")
                        
                    except ValueError:
                        pass  # 잘못된 프레임 값은 무시
            
        except Exception as e:
            pass
    
    def _calculate_velocity_values(self):
        """5열 속도 값 자동 계산 - 병합된 셀에 km/h 단위로 표시"""
        try:
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            if not fps_value:
                return
            
            fps = float(fps_value)
            
            # 각 구간별로 계산 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                segment_start_row = row  # 구간 시작 행
                
                # 프레임 정보와 거리 정보 가져오기 (병합된 셀에서)
                start_frame = self._get_cell_value(segment_start_row, 1)
                end_frame = self._get_cell_value(segment_start_row, 2)
                distance = self._get_cell_value(segment_start_row, 3)
                
                if start_frame and end_frame and distance:
                    try:
                        start_f = float(start_frame)
                        end_f = float(end_frame)
                        dist = float(distance)
                        
                        # 구간 시간 계산 (초 단위)
                        segment_time = (end_f - start_f) / fps
                        
                        if segment_time > 0:
                            # 속도 계산 (m/s)
                            velocity_ms = dist / segment_time
                            
                            # m/s를 km/h로 변환
                            velocity_kmh = velocity_ms * 3.6
                            
                            # 병합된 셀에 속도 설정 (소수점 둘째자리까지)
                            vel_item = self.main_table.item(segment_start_row, 5)
                            if vel_item:
                                vel_item.setText(f"{velocity_kmh:.2f}")
                        
                    except (ValueError, ZeroDivisionError):
                        pass  # 잘못된 값은 무시
            
        except Exception as e:
            pass
    
    def _calculate_segment_time_values(self, start_row):
        """특정 구간의 4열 시간 값 계산 - 병합된 셀"""
        try:
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            if not fps_value:
                return
            
            fps = float(fps_value)
            segment_index = (start_row - 2) // 2
            segment_start_row = start_row  # 구간 시작 행
            
            # 프레임 정보 가져오기 (병합된 셀에서)
            start_frame = self._get_cell_value(segment_start_row, 1)
            end_frame = self._get_cell_value(segment_start_row, 2)
            
            if start_frame and end_frame:
                try:
                    start_f = float(start_frame)
                    end_f = float(end_frame)
                    
                    # 구간 시간 계산
                    segment_time = (end_f - start_f) / fps
                    
                    # 누적 시간 계산
                    if segment_index == 0:
                        # 1구간은 0부터 시작
                        time_cumulative = 0.000
                    else:
                        # 이전 구간의 종료 시간 가져오기
                        prev_segment_start_row = start_row - 2
                        prev_time_str = self._get_cell_value(prev_segment_start_row, 4)
                        time_cumulative = float(prev_time_str) if prev_time_str else 0.0
                    
                    # 구간 종료 시간 계산
                    time_end = time_cumulative + segment_time
                    
                    # 병합된 셀에 구간 종료 시간 설정 (소수점 셋째자리까지)
                    time_item = self.main_table.item(segment_start_row, 4)
                    if time_item:
                        time_item.setText(f"{time_end:.3f}")
                    
                except ValueError:
                    pass  # 잘못된 프레임 값은 무시
            
        except Exception as e:
            pass
    
    def _calculate_segment_velocity_values(self, start_row):
        """특정 구간의 5열 속도 값 계산 - 병합된 셀에 km/h 단위로 표시"""
        try:
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            if not fps_value:
                return
            
            fps = float(fps_value)
            segment_start_row = start_row  # 구간 시작 행
            
            # 프레임 정보와 거리 정보 가져오기 (병합된 셀에서)
            start_frame = self._get_cell_value(segment_start_row, 1)
            end_frame = self._get_cell_value(segment_start_row, 2)
            distance = self._get_cell_value(segment_start_row, 3)
            
            if start_frame and end_frame and distance:
                try:
                    start_f = float(start_frame)
                    end_f = float(end_frame)
                    dist = float(distance)
                    
                    # 구간 시간 계산 (초 단위)
                    segment_time = (end_f - start_f) / fps
                    
                    if segment_time > 0:
                        # 속도 계산 (m/s)
                        velocity_ms = dist / segment_time
                        
                        # m/s를 km/h로 변환
                        velocity_kmh = velocity_ms * 3.6
                        
                        # 병합된 셀에 속도 설정 (소수점 둘째자리까지)
                        vel_item = self.main_table.item(segment_start_row, 5)
                        if vel_item:
                            vel_item.setText(f"{velocity_kmh:.2f}")
                    
                except (ValueError, ZeroDivisionError):
                    pass  # 잘못된 값은 무시
            
        except Exception as e:
            pass
    
    def _calculate_acc_time_values(self):
        """6열 가속도 적용 시간 자동 계산"""
        try:
            # 각 구간별로 계산 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                segment_start_row = row      # 구간 시작 행 (윗셀)
                segment_end_row = row + 1    # 구간 끝 행 (아랫셀)
                segment_index = (row - 2) // 2
                
                # 윗셀: 이전구간의 time 값 (1구간은 0.000)
                if segment_index == 0:
                    prev_time = "0.000"
                else:
                    prev_segment_row = row - 2
                    prev_time = self._get_cell_value(prev_segment_row, 4)
                    if not prev_time:
                        prev_time = "0.000"
                
                # 아랫셀: 현재구간의 time 값
                curr_time = self._get_cell_value(segment_start_row, 4)
                if not curr_time:
                    curr_time = "0.000"
                
                # 6열에 값 설정
                start_time_item = self.main_table.item(segment_start_row, 6)
                end_time_item = self.main_table.item(segment_end_row, 6)
                
                if start_time_item:
                    start_time_item.setText(prev_time)
                if end_time_item:
                    end_time_item.setText(curr_time)
                

            
        except Exception as e:
            pass
    
    def _calculate_segment_acc_time_values(self, start_row):
        """특정 구간의 6열 가속도 적용 시간 계산"""
        try:
            segment_start_row = start_row      # 구간 시작 행 (윗셀)
            segment_end_row = start_row + 1    # 구간 끝 행 (아랫셀)
            segment_index = (start_row - 2) // 2
            
            # 윗셀: 이전구간의 time 값 (1구간은 0.000)
            if segment_index == 0:
                prev_time = "0.000"
            else:
                prev_segment_row = start_row - 2
                prev_time = self._get_cell_value(prev_segment_row, 4)
                if not prev_time:
                    prev_time = "0.000"
            
            # 아랫셀: 현재구간의 time 값
            curr_time = self._get_cell_value(segment_start_row, 4)
            if not curr_time:
                curr_time = "0.000"
            
            # 6열에 값 설정
            start_time_item = self.main_table.item(segment_start_row, 6)
            end_time_item = self.main_table.item(segment_end_row, 6)
            
            if start_time_item:
                start_time_item.setText(prev_time)
            if end_time_item:
                end_time_item.setText(curr_time)
            

            
        except Exception as e:
            pass
    
    def _update_columns_7_to_10_only(self, segments):
        """그래프에서 온 업데이트 시 7~10열만 업데이트"""
        try:
            
            # 시그널 연결 일시 해제 (무한 루프 방지)
            try:
                self.main_table.itemChanged.disconnect(self._on_table_item_changed)
            except TypeError:
                pass
            
            # 각 구간별로 7~10열 업데이트
            for i, segment in enumerate(segments):
                row = 2 + (i * 2)  # 구간 시작 행
                
                if row >= self.main_table.rowCount():
                    break
                
                # 7열: acc_velocity (가속도 속도)
                acc_velocity = segment.get('acc_velocity', '')
                if acc_velocity != '':
                    item = self.main_table.item(row, 7)
                    if item:
                        item.setText(str(acc_velocity))
                    else:
                        item = QTableWidgetItem(str(acc_velocity))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        self.main_table.setItem(row, 7, item)
                
                # 8열: acceleration (가속도)
                acceleration = segment.get('acceleration', '')
                if acceleration != '':
                    item = self.main_table.item(row, 8)
                    if item:
                        item.setText(str(acceleration))
                    else:
                        item = QTableWidgetItem(str(acceleration))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        self.main_table.setItem(row, 8, item)
                
                # 9열: duration (지속시간)
                duration = segment.get('duration', '')
                if duration != '':
                    item = self.main_table.item(row, 9)
                    if item:
                        item.setText(str(duration))
                    else:
                        item = QTableWidgetItem(str(duration))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        self.main_table.setItem(row, 9, item)
                
                # 10열: acc_dec_type (가속/감속 타입)
                acc_dec_type = segment.get('acc_dec_type', '')
                if acc_dec_type != '':
                    item = self.main_table.item(row, 10)
                    if item:
                        item.setText(str(acc_dec_type))
                    else:
                        item = QTableWidgetItem(str(acc_dec_type))
                        item.setTextAlignment(Qt.AlignCenter)
                        # 유효성에 따른 색상 설정
                        if 'Invalid' in acc_dec_type:
                            item.setBackground(QBrush(QColor(255, 200, 200)))  # 연한 빨강
                        else:
                            item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        self.main_table.setItem(row, 10, item)
            
            # 시그널 재연결
            self.main_table.itemChanged.connect(self._on_table_item_changed)
            
            
        except Exception as e:
            pass
            # 에러 발생 시에도 시그널 재연결
            try:
                self.main_table.itemChanged.connect(self._on_table_item_changed)
            except:
                pass
    
    def _update_optimization_velocity_column(self, optimization_data):
        """7열에 최적화 그래프 속도 데이터 연동"""
        try:
            if not optimization_data:
                return
            

            
            # 시그널 연결 일시 해제 (무한 루프 방지)
            try:
                self.main_table.itemChanged.disconnect(self._on_table_item_changed)
            except TypeError:
                # 이미 연결이 해제되어 있거나 연결된 적이 없는 경우
                pass
            
            # 각 구간별로 처리 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                segment_start_row = row      # 구간 시작 행 (윗셀)
                segment_end_row = row + 1    # 구간 끝 행 (아랫셀)
                segment_index = (row - 2) // 2
                

                
                # 해당 구간에 대응하는 최적화 데이터가 있는지 확인
                if segment_index < len(optimization_data):
                    # 구간 시작점 속도 (윗셀)
                    data_index = segment_index * 2  # 실제 데이터 인덱스 (0,2,4,6,8)
                    if data_index < len(optimization_data):
                        start_velocity = optimization_data[data_index].get('velocity', 0.0)
                        start_vel_item = self.main_table.item(segment_start_row, 7)
                        if start_vel_item:
                            start_vel_item.setText(f"{start_velocity:.2f}")
                        

                    
                    # 구간 끝점 속도 (아랫셀) - 다음 데이터 포인트
                    end_data_index = segment_index * 2 + 1  # 실제 데이터 인덱스 (1,3,5,7,9)
                    if end_data_index < len(optimization_data):
                        end_velocity = optimization_data[end_data_index].get('velocity', 0.0)
                        end_vel_item = self.main_table.item(segment_end_row, 7)
                        if end_vel_item:
                            end_vel_item.setText(f"{end_velocity:.2f}")
                        

                    else:
                        # 마지막 구간의 경우 끝점은 마지막 포인트와 동일
                        end_vel_item = self.main_table.item(segment_end_row, 7)
                        if end_vel_item:
                            end_vel_item.setText(f"{start_velocity:.2f}")
                        

            
            # 시그널 연결 복구
            try:
                self.main_table.itemChanged.connect(self._on_table_item_changed)
            except TypeError:
                # 이미 연결되어 있는 경우
                pass
            

            
        except Exception as e:
            pass
            # 시그널 연결 복구 (에러 시에도)
            try:
                self.main_table.itemChanged.connect(self._on_table_item_changed)
            except:
                pass
    
    def _update_acc_dec_color(self, row):
        """10열 가속도/감속도 유효성 색상 업데이트"""
        try:
            # 8열 가속도 값 가져오기
            acc_value = self._get_cell_value(row, 8)
            if not acc_value:
                return
            
            try:
                acceleration = float(acc_value)
            except:
                return
            
            # FPS 테이블에서 가속도 한계값 가져오기
            max_acc_value = self._get_cell_value_from_table(self.fps_table, 1, 1)
            max_dec_value = self._get_cell_value_from_table(self.fps_table, 2, 1)
            
            max_acc = float(max_acc_value) if max_acc_value else 3.5
            max_dec = float(max_dec_value) if max_dec_value else -7.85
            
            # 가속도 유효성 판단 및 텍스트/색상 설정
            uniform_threshold = DEFAULT_UNIFORM_MOTION_THRESHOLD  # 추후 옵션으로 확장 가능
            
            if abs(acceleration) <= uniform_threshold:
                # 등속 구간 (임계값 이하)
                text = "Const (Uniform)"
                color = ACCELERATION_UNIFORM_CELL_COLOR
            elif acceleration > uniform_threshold:
                # 가속 구간
                if acceleration <= max_acc:
                    # Valid 가속
                    text = "Acc (Valid)"
                    color = ACCELERATION_VALID_CELL_COLOR
                else:
                    # Invalid 가속
                    text = "Acc (Invalid)"
                    color = ACCELERATION_INVALID_CELL_COLOR
            else:  # acceleration < -uniform_threshold
                # 감속 구간
                if acceleration >= max_dec:
                    # Valid 감속
                    text = "Dec (Valid)"
                    color = ACCELERATION_VALID_CELL_COLOR
                else:
                    # Invalid 감속
                    text = "Dec (Invalid)"
                    color = ACCELERATION_INVALID_CELL_COLOR
            
            # 10열 아이템 가져오기 또는 생성
            item_10 = self.main_table.item(row, 10)
            if not item_10:
                item_10 = QTableWidgetItem(text)
                item_10.setTextAlignment(Qt.AlignCenter)
                self.main_table.setItem(row, 10, item_10)
                self.main_table.setSpan(row, 10, 2, 1)
            else:
                item_10.setText(text)
            
            # 색상 적용
            item_10.setBackground(QBrush(QColor(color)))
                
        except Exception as e:
            pass
    
    def _check_and_calculate_auto_values(self):
        """사용자 입력 데이터가 완성된 구간별로 자동 계산 실행"""
        try:
            # FPS 값 확인
            fps_value = self._get_cell_value_from_table(self.fps_table, 0, 1)
            if not fps_value:
                return
            
            # 각 구간별로 개별 계산
            for row in range(2, self.main_table.rowCount(), 2):
                segment_start_row = row  # 구간 시작 행
                
                # 해당 구간의 필수 입력 값들 확인 (START, END, 거리)
                start_frame = self._get_cell_value(segment_start_row, 1)
                end_frame = self._get_cell_value(segment_start_row, 2)
                distance = self._get_cell_value(segment_start_row, 3)
                
                # 해당 구간의 조건이 충족되면 계산 실행
                if start_frame and end_frame and distance:
                    self._calculate_segment_time_values(row)
                    self._calculate_segment_velocity_values(row)
                    self._calculate_segment_acc_time_values(row)  # 6열 가속도 시간 계산 추가

            
        except Exception as e:
            pass
    
    # === 데이터 수집 및 새로고침 메서드 ===
    
    def _collect_and_send_table_data(self):
        """테이블 데이터 수집 후 Data Bridge로 전송"""
        try:

            segments_data = []
            
            # 메인 테이블에서 구간별 데이터 처리 (2행씩 그룹)
            for row in range(2, self.main_table.rowCount(), 2):
                segment_start_row = row      # 구간 시작 행 (주요 병합된 데이터)
                segment_end_row = row + 1    # 구간 끝 행 (끝 상태 데이터)
                
                # 각 구간의 데이터 추출
                segment_data = {}
                
                # 사용자 입력 데이터만 수집 (1-6열) - 7-10열 제외하여 무한 루프 방지
                segment_data['segment_num'] = self._get_cell_value(segment_start_row, 0)
                segment_data['frame_start'] = self._get_cell_value(segment_start_row, 1)
                segment_data['frame_end'] = self._get_cell_value(segment_start_row, 2)
                segment_data['distance'] = self._get_cell_value(segment_start_row, 3)
                segment_data['avg_velocity'] = self._get_cell_value(segment_start_row, 5)  # 병합된 셀 - 시작 행에서 읽기
                
                # 시간 관련 데이터 (4, 6열)
                segment_data['avg_time'] = self._get_cell_value(segment_start_row, 4)  # 시작 상태 시간
                segment_data['acc_time'] = self._get_cell_value(segment_start_row, 6)   # 시작 상태 가속시간
                
                # 7-10열은 제외 (시스템 계산 값): acc_velocity, acceleration, duration, acc_dec_type
                # 이 값들은 DataBridge에서 계산되어 다시 테이블로 전송되므로 무한 루프 방지를 위해 제외
                
                # 디버깅: 수집된 데이터 확인
                segment_num = (segment_start_row - 2) // 2 + 1

                
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
                
                # 디버깅: DataBridge로 전송되는 데이터 확인


                for i, segment in enumerate(segments_data):
                    pass
                
                self.data_bridge.update_from_table(table_data)

            
        except Exception as e:
            pass
    
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
            
            # 세그먼트 데이터 행 추가 (각 세그먼트당 2행)
            for i, segment in enumerate(segments):
                start_row = 2 + (i * 2)  # 헤더 다음부터, 각 세그먼트당 2행
                
                # 2행 추가 (Time 행, Vel 행)
                self.main_table.insertRow(start_row)
                self.main_table.insertRow(start_row + 1)
                
                segment_start_row = start_row  # 구간 시작 행 (주요 병합된 데이터)
                segment_end_row = start_row + 1   # 구간 끝 행 (끝 상태 데이터)
                
                # 병합 대상 열 (0, 1, 2, 3, 4, 5, 8, 9, 10)
                merge_columns = [0, 1, 2, 3, 4, 5, 8, 9, 10]
                
                for col in range(11):
                    if col in merge_columns:
                        # 병합 대상 열: Time 행에만 값 설정하고 rowspan=2 적용
                        value = ""
                        if col == 0:
                            value = str(segment.get('segment_num', i + 1))
                        elif col == 1:
                            value = str(segment.get('frame_start', ''))
                        elif col == 2:
                            value = str(segment.get('frame_end', ''))
                        elif col == 3:
                            value = str(segment.get('distance', ''))
                        elif col == 4:
                            value = str(segment.get('avg_time', ''))
                        elif col == 5:
                            value = str(segment.get('avg_velocity', ''))
                        elif col == 8:
                            value = str(segment.get('acceleration', ''))
                        elif col == 9:
                            duration_val = segment.get('duration', '')
                            if duration_val and duration_val != '':
                                try:
                                    value = f"{float(duration_val):.3f}"
                                except:
                                    value = str(duration_val)
                            else:
                                value = ''
                        elif col == 10:
                            acc_dec_type = segment.get('acc_dec_type', '')
                            # 텍스트와 색상을 동시에 표시
                            value = str(acc_dec_type)
                        
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignCenter)
                        
                        # 색상 설정
                        if col in [1, 2, 8]:  # 사용자 입력
                            item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
                        elif col == 3:  # PC-Crash 연동
                            item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
                        elif col == 9:  # Duration 자동 계산
                            item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        elif col == 10:  # Acc/Dec/Const 유효성 색상 표시
                            if 'Uniform' in acc_dec_type:
                                item.setBackground(QBrush(QColor(ACCELERATION_UNIFORM_CELL_COLOR)))
                            elif 'Valid' in acc_dec_type:
                                item.setBackground(QBrush(QColor(ACCELERATION_VALID_CELL_COLOR)))
                            elif 'Invalid' in acc_dec_type:
                                item.setBackground(QBrush(QColor(ACCELERATION_INVALID_CELL_COLOR)))
                            else:
                                item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        elif col in [4, 5]:  # 기타 자동 계산
                            item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        
                        self.main_table.setItem(segment_start_row, col, item)
                        # setSpan으로 셀 병합 (row, col, rowspan, colspan)
                        self.main_table.setSpan(segment_start_row, col, 2, 1)
                        
                    else:
                        # 병합하지 않는 열 (6, 7): 각 행에 개별 값 설정
                        # Time 행 (윗셀 - 구간 시작)
                        time_value = ""
                        if col == 6:
                            time_value = str(segment.get('acc_time', ''))
                        elif col == 7:
                            # 7열 윗셀: 최적화 속도 (구간 시작점) - 임시 빈값으로 설정 (나중에 그래프 데이터로 업데이트)
                            time_value = ""
                        
                        time_item = QTableWidgetItem(time_value)
                        time_item.setTextAlignment(Qt.AlignCenter)
                        
                        # 색상 규칙 적용
                        # 6열: 자동 계산 색상 (가속도 적용 시간)
                        # 7열: 자동 계산 색상 (최적화 속도)
                        if col == 6:  # acc_time은 자동 계산
                            time_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                            time_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        
                        self.main_table.setItem(segment_start_row, col, time_item)
                        
                        # Vel 행 (아랫셀 - 구간 끝)
                        vel_value = ""
                        if col == 6:
                            vel_value = ""  # 6열 아랫셀은 사용하지 않음
                        elif col == 7:
                            # 7열 아랫셀: 최적화 속도 (구간 끝점) - 임시 빈값으로 설정 (나중에 그래프 데이터로 업데이트)
                            vel_value = ""
                        
                        vel_item = QTableWidgetItem(vel_value)
                        vel_item.setTextAlignment(Qt.AlignCenter)
                        
                        # 색상 규칙 적용
                        # 6열: 자동 계산 색상 (가속도 적용 시간)
                        # 7열: 자동 계산 색상 (최적화 속도)
                        if col == 6:  # acc_time은 자동 계산
                            vel_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                            vel_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                        
                        self.main_table.setItem(segment_end_row, col, vel_item)
                
                # 행 높이 설정
                self.main_table.setRowHeight(segment_start_row, 30)
                self.main_table.setRowHeight(segment_end_row, 30)
            
            # FPS 값 설정
            fps_value = settings.get('fps', 30.0)
            fps_item = self.fps_table.item(0, 1)
            if fps_item:
                fps_item.setText(str(fps_value))
            

            
        except Exception as e:
            pass
    
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
    
    # === 프리셋 데이터 및 로드 메서드 ===
    
    def _get_preset1_data(self):
        """프리셋1 테스트 데이터 - 사용자 제공 데이터"""
        return {
            'fps': 30.0,
            'segments': [
                {
                    'segment_num': 1,
                    'frame_start': '478',
                    'frame_end': '610',
                    'distance': '95.54',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 2,
                    'frame_start': '610',
                    'frame_end': '725',
                    'distance': '81.01',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 3,
                    'frame_start': '725',
                    'frame_end': '858',
                    'distance': '83.08',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 4,
                    'frame_start': '858',
                    'frame_end': '961',
                    'distance': '61.28',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 5,
                    'frame_start': '961',
                    'frame_end': '1080',
                    'distance': '69.73',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                }
            ]
        }
    
    def _get_preset2_data(self):
        """프리셋2 테스트 데이터 - 사용자 제공 데이터"""
        return {
            'fps': 30.0,
            'segments': [
                {
                    'segment_num': 1,
                    'frame_start': '620',
                    'frame_end': '650',
                    'distance': '8.64',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 2,
                    'frame_start': '650',
                    'frame_end': '680',
                    'distance': '8.64',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 3,
                    'frame_start': '680',
                    'frame_end': '710',
                    'distance': '7.58',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 4,
                    'frame_start': '710',
                    'frame_end': '740',
                    'distance': '6.60',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 5,
                    'frame_start': '740',
                    'frame_end': '770',
                    'distance': '6.15',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 6,
                    'frame_start': '770',
                    'frame_end': '800',
                    'distance': '5.59',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 7,
                    'frame_start': '800',
                    'frame_end': '830',
                    'distance': '5.13',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 8,
                    'frame_start': '830',
                    'frame_end': '860',
                    'distance': '4.61',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 9,
                    'frame_start': '860',
                    'frame_end': '890',
                    'distance': '5.54',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 10,
                    'frame_start': '890',
                    'frame_end': '920',
                    'distance': '4.81',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                },
                {
                    'segment_num': 11,
                    'frame_start': '920',
                    'frame_end': '950',
                    'distance': '5.36',
                    'acceleration': '',
                    'acc_time': '',
                    'acc_velocity': ''
                }
            ]
        }
    
    def _load_preset1(self):
        """프리셋1 데이터 로드"""
        try:

            preset_data = self._get_preset1_data()
            self._apply_preset_data(preset_data)
            self._show_info_message("프리셋 로드", "프리셋1 데이터가 성공적으로 로드되었습니다.")

            
        except Exception as e:
            pass
            self._show_error_message("프리셋 로드 오류", f"프리셋1 로드 중 오류가 발생했습니다: {e}")
    
    def _load_preset2(self):
        """프리셋2 데이터 로드"""
        try:

            preset_data = self._get_preset2_data()
            self._apply_preset_data(preset_data)
            self._show_info_message("프리셋 로드", "프리셋2 데이터가 성공적으로 로드되었습니다.")

            
        except Exception as e:
            pass
            self._show_error_message("프리셋 로드 오류", f"프리셋2 로드 중 오류가 발생했습니다: {e}")
    
    def _apply_preset_data(self, preset_data):
        """프리셋 데이터를 테이블에 적용"""
        try:
            # 테이블 아이템 변경 시그널 임시 차단
            self.main_table.itemChanged.disconnect()
            self.fps_table.itemChanged.disconnect()
            
            # FPS 값 설정
            fps_item = self.fps_table.item(0, 1)
            if fps_item:
                fps_item.setText(str(preset_data['fps']))
            
            # 기존 구간들 제거 (헤더 2행 제외하고 모든 행 삭제)
            while self.main_table.rowCount() > 2:
                self.main_table.removeRow(2)
            
            # 프리셋 구간 데이터 추가
            for segment in preset_data['segments']:
                self._add_preset_segment(segment)
            
            # 자동 계산 실행
            self._check_and_calculate_auto_values()
            
            # Qt 이벤트 처리 대기 (UI 업데이트 완료 보장)
            QApplication.processEvents()
            
            # 디버깅: 자동 계산 후 실제 테이블 값 확인

            for row in range(2, self.main_table.rowCount(), 2):
                segment_num = (row - 2) // 2 + 1
                avg_time = self._get_cell_value(row, 4)
                avg_velocity = self._get_cell_value(row, 5)

            
            # 데이터 수집 및 전송
            self._collect_and_send_table_data()
            
            # 시그널 다시 연결
            self.main_table.itemChanged.connect(self._on_table_item_changed)
            self.fps_table.itemChanged.connect(self._on_fps_changed)
            

            
        except Exception as e:
            pass
            # 시그널 다시 연결 (에러 시에도)
            self.main_table.itemChanged.connect(self._on_table_item_changed)
            self.fps_table.itemChanged.connect(self._on_fps_changed)
            raise
    
    def _add_preset_segment(self, segment_data):
        """프리셋 구간 데이터를 테이블에 추가"""
        try:
            # 새 구간을 위한 행 2개 추가
            current_row = self.main_table.rowCount()
            self.main_table.insertRow(current_row)
            self.main_table.insertRow(current_row + 1)
            
            segment_start_row = current_row      # 구간 시작 행 (주요 병합된 데이터)
            segment_end_row = current_row + 1    # 구간 끝 행 (끝 상태 데이터)
            
            # 병합 대상 열 (0, 1, 2, 3, 4, 5, 8, 9, 10) - Time과 Vel도 병합 추가
            merge_columns = [0, 1, 2, 3, 4, 5, 8, 9, 10]
            
            for col in range(11):
                if col in merge_columns:
                    # 병합 대상 열: Time 행에만 값 설정하고 rowspan=2 적용
                    value = ""
                    if col == 0:
                        value = str(segment_data.get('segment_num', ''))
                    elif col == 1:
                        value = str(segment_data.get('frame_start', ''))
                    elif col == 2:
                        value = str(segment_data.get('frame_end', ''))
                    elif col == 3:
                        value = str(segment_data.get('distance', ''))
                    elif col == 8:
                        value = str(segment_data.get('acceleration', ''))
                    elif col == 9:
                        duration_val = segment_data.get('duration', '')
                        if duration_val and duration_val != '':
                            try:
                                value = f"{float(duration_val):.3f}"
                            except:
                                value = str(duration_val)
                        else:
                            value = ''
                    elif col == 10:
                        acc_dec_type = segment_data.get('acc_dec_type', '')
                        # 텍스트와 색상을 동시에 표시
                        value = str(acc_dec_type)
                    
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # 색상 설정
                    if col in [1, 2, 8]:  # 사용자 입력
                        item.setBackground(QBrush(QColor(USER_INPUT_COLOR)))
                    elif col == 3:  # PC-Crash 연동
                        item.setBackground(QBrush(QColor(PC_CRASH_INTEGRATION_COLOR)))
                    elif col == 9:  # Duration 자동 계산
                        item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    elif col == 10:  # Acc/Dec/Const 유효성 색상 표시
                        if 'Uniform' in acc_dec_type:
                            item.setBackground(QBrush(QColor(ACCELERATION_UNIFORM_CELL_COLOR)))
                        elif 'Valid' in acc_dec_type:
                            item.setBackground(QBrush(QColor(ACCELERATION_VALID_CELL_COLOR)))
                        elif 'Invalid' in acc_dec_type:
                            item.setBackground(QBrush(QColor(ACCELERATION_INVALID_CELL_COLOR)))
                        else:
                            item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    elif col in [4, 5]:  # 기타 자동 계산
                        item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    
                    self.main_table.setItem(segment_start_row, col, item)
                    # setSpan으로 셀 병합 (row, col, rowspan, colspan)
                    self.main_table.setSpan(segment_start_row, col, 2, 1)
                    
                else:
                    # 병합하지 않는 열 (6, 7): 각 행에 개별 값 설정
                    # Time 행 (윗셀 - 구간 시작)
                    time_value = ""
                    if col == 6:
                        time_value = str(segment_data.get('acc_time', ''))
                    elif col == 7:
                        # 7열 윗셀: 최적화 속도 (구간 시작점) - 임시 빈값으로 설정 (나중에 그래프 데이터로 업데이트)
                        time_value = ""
                    
                    time_item = QTableWidgetItem(time_value)
                    time_item.setTextAlignment(Qt.AlignCenter)
                    
                    # 색상 규칙 적용
                    # 6열: 자동 계산 색상 (가속도 적용 시간)
                    # 7열: 자동 계산 색상 (최적화 속도)
                    if col == 6:  # acc_time은 자동 계산
                        time_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                        time_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    
                    self.main_table.setItem(segment_start_row, col, time_item)
                    
                    # Vel 행 (아랫셀 - 구간 끝)
                    vel_value = ""
                    if col == 6:
                        vel_value = ""  # 6열 아랫셀은 사용하지 않음
                    elif col == 7:
                        # 7열 아랫셀: 최적화 속도 (구간 끝점) - 임시 빈값으로 설정 (나중에 그래프 데이터로 업데이트)
                        vel_value = ""
                    
                    vel_item = QTableWidgetItem(vel_value)
                    vel_item.setTextAlignment(Qt.AlignCenter)
                    
                    # 색상 규칙 적용
                    # 6열: 자동 계산 색상 (가속도 적용 시간)
                    # 7열: 자동 계산 색상 (최적화 속도)
                    if col == 6:  # acc_time은 자동 계산
                        vel_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    elif col == 7:  # acc_velocity는 자동 계산 (최적화 그래프 연동)
                        vel_item.setBackground(QBrush(QColor(AUTO_CALCULATION_COLOR)))
                    
                    self.main_table.setItem(segment_end_row, col, vel_item)
            
            # 행 높이 설정
            self.main_table.setRowHeight(segment_start_row, 30)
            self.main_table.setRowHeight(segment_end_row, 30)
            

            
        except Exception as e:
            pass
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        self.window_closing.emit()
        event.accept()