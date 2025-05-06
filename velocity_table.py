# velocity_table.py 최상단
import sys
from PyQt5.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem, 
                           QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QWidget)
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QColor, QBrush

class TableWindow(QMainWindow):
    def __init__(self, data_bridge=None):  # data_bridge 파라미터 추가
        super().__init__()
        self.data_bridge = data_bridge     # data_bridge 저장
        self.setWindowTitle("추가 병합된 셀을 가진 테이블")
        self.setGeometry(100, 100, 1143, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 여백 추가
        main_layout.setContentsMargins(20, 20, 20, 20)  # 좌, 상, 우, 하 여백
        main_layout.setSpacing(20)  # 위젯 간 간격

        self.table = QTableWidget(self)
        main_layout.addWidget(self.table)

        # 하단 테이블들을 위한 수평 레이아웃
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)  # 하단 테이블 간 간격 설정
        
        # FPS 표 추가
        self.fps_table = QTableWidget(self)
        bottom_layout.addWidget(self.fps_table)
        
        # FPS 표와 info_table 사이에 스트레�� 추가
        bottom_layout.addStretch(1)
        
        # 새로운 3x1 표 추가 (오른쪽 정렬)
        self.info_table = QTableWidget(self)
        bottom_layout.addWidget(self.info_table)
        
        # 하단 레이아웃을 메인 레이아웃에 추가
        main_layout.addLayout(bottom_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 버튼 간 간격
        self.add_button = QPushButton("+", self)
        self.add_button.clicked.connect(self.add_new_block)
        self.remove_button = QPushButton("-", self)
        self.remove_button.clicked.connect(self.remove_block)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.header_rows = 2  # 헤더 행 수
        self.block_rows = 2   # 단위 블록의 행 수
        self.total_cols = 11  # 열 수
        self.data_blocks = 2  # 초기 데이터 블록 수

        self.table.itemChanged.connect(self.on_cell_changed)
        self.fps_table.itemChanged.connect(self.on_fps_changed)

        self.create_table()
        self.create_fps_table()
        self.create_info_table()
        self.update_remove_button()

    def create_table(self):
        total_rows = self.header_rows + self.block_rows * self.data_blocks
        self.table.setRowCount(total_rows)
        self.table.setColumnCount(self.total_cols)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)

        self.set_headers()
        
        for i in range(self.data_blocks):
            self.add_data_block(i)

        for col in range(self.total_cols):
            self.table.setColumnWidth(col, 100)
        
        for row in range(total_rows):
            self.table.setRowHeight(row, 50 if row < self.header_rows else 23)

        # 첫 번째 블록 설정
        self.set_block_colors(2)

        # 두 번째 블록 설정
        self.set_block_colors(4, start_color="#FCE4D6", is_first_block=False)

        self.set_editable_cells()
        self.update_acc_time_cells()  # 가속도 적용 time 셀 초기화

    def set_editable_cells(self):
        editable_cells = [(row, col) for row in range(2, self.table.rowCount(), 2) 
                          for col in [1, 2, 3, 8, 9]]
        for row, col in editable_cells:
            item = self.table.item(row, col)
            if item:
                item.setFlags(item.flags() | Qt.ItemIsEditable)

    def on_cell_changed(self, item):
        row = item.row()
        col = item.column()
        
        # 셀 선택 해제
        self.table.setCurrentItem(None)
        
        if col in [1, 2, 3] and row % 2 == 0:  # START, END, 거리 열이 변경됨 (짝수 행)
            self.update_time_cell(row)
            self.update_vel_cell(row)
            self.update_acc_time_cell(row)
            next_row = row + 2
            while next_row < self.table.rowCount():
                self.update_time_cell(next_row)
                self.update_vel_cell(next_row)
                self.update_acc_time_cell(next_row)
                next_row += 2
        if col == 2 and row % 2 == 0:  # END 열이 변경됨 (짝수 행)
            self.update_next_start(row)
            
        # 데이터 브릿지에 업데이트 알림 추가
        if self.data_bridge:
            table_data = self.get_table_data()
            self.data_bridge.update_from_table(table_data)

    def on_fps_changed(self, item):
        if item.column() == 1:  # FPS 값이 변경됨
            self.update_all_time_cells()

    def update_time_cell(self, row):
        start_item = self.table.item(row, 1)
        end_item = self.table.item(row, 2)
        fps_item = self.fps_table.item(0, 1)
        time_item = self.table.item(row + 1, 4)  # time 값을 아래 셀에 입력

        if start_item and end_item and fps_item and time_item:
            try:
                start = int(start_item.text())
                end = int(end_item.text())
                fps = float(fps_item.text())
                
                # 이전 블록의 time 값 가져오기
                prev_time = 0
                if row > 2:  # 첫 번째 블록이 아닌 경우
                    prev_time_item = self.table.item(row - 1, 4)
                    if prev_time_item:
                        prev_time = float(prev_time_item.text())
                
                # 새로운 time 값 계산 (소수점 셋째 자리까지)
                new_time = round((end - start) * (1 / fps) + prev_time, 3)
                time_item.setText(f"{new_time:.3f}")
            except ValueError:
                pass  # 유효하지 않은 입력 처리

    def update_next_start(self, row):
        current_end_item = self.table.item(row, 2)
        next_start_item = self.table.item(row + 2, 1) if row + 2 < self.table.rowCount() else None

        if current_end_item and next_start_item:
            next_start_item.setText(current_end_item.text())

    def update_all_time_cells(self):
        for row in range(2, self.table.rowCount(), 2):
            self.update_time_cell(row)
            self.update_acc_time_cell(row)  # 가속도 적용 time 셀 업데이트

    def create_fps_table(self):
        self.fps_table.setRowCount(1)
        self.fps_table.setColumnCount(2)
        self.fps_table.setFixedHeight(35)
        self.fps_table.setFixedWidth(202)  # 너비 고정

        self.fps_table.verticalHeader().setVisible(False)
        self.fps_table.horizontalHeader().setVisible(False)

        item = QTableWidgetItem("FPS")
        item.setTextAlignment(Qt.AlignCenter)
        self.fps_table.setItem(0, 0, item)

        fps_input_item = QTableWidgetItem()
        fps_input_item.setBackground(QBrush(QColor("#E2EFDA")))
        fps_input_item.setTextAlignment(Qt.AlignCenter)
        self.fps_table.setItem(0, 1, fps_input_item)

        self.fps_table.setColumnWidth(0, 100)
        self.fps_table.setColumnWidth(1, 100)
        self.fps_table.setRowHeight(0, 35)

    def create_info_table(self):
        self.info_table.setRowCount(1)
        self.info_table.setColumnCount(3)
        self.info_table.setFixedHeight(35)
        self.info_table.setFixedWidth(302)

        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setVisible(False)

        items = ["사용자 입력", "자동계산", "PCC 연동"]
        colors = ["#E2EFDA", "#FCE4D6", "#FFF2CC"]
        
        for col, (text, color) in enumerate(zip(items, colors)):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QBrush(QColor(color)))
            self.info_table.setItem(0, col, item)

        for col in range(3):
            self.info_table.setColumnWidth(col, 100)
        self.info_table.setRowHeight(0, 35)

    def set_headers(self):
        self.merge_cells(0, 0, 2, 1, "구간")
        self.merge_cells(0, 1, 2, 1, "START")
        self.merge_cells(0, 2, 2, 1, "END")
        self.merge_cells(0, 3, 2, 1, "거리")
        self.merge_cells(0, 4, 1, 2, "구간별 평균속도")
        self.merge_cells(0, 6, 1, 2, "가속도 적용")
        self.merge_cells(0, 8, 2, 1, "Acc")
        self.merge_cells(0, 9, 2, 1, "Duration")
        self.merge_cells(0, 10, 2, 1, "Acc/Dec")

        self.set_cell(1, 4, "Time")
        self.set_cell(1, 5, "Vel")
        self.set_cell(1, 6, "Time")
        self.set_cell(1, 7, "Vel")

    def add_data_block(self, block_index):
        start_row = self.header_rows + block_index * self.block_rows
        for col in [0, 1, 2, 3, 8, 9, 10]:
            self.merge_cells(start_row, col, self.block_rows, 1, "")

    def merge_cells(self, row, col, rowspan, colspan, text):
        self.table.setSpan(row, col, rowspan, colspan)
        merged_item = QTableWidgetItem(text)
        merged_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, merged_item)

    def set_cell(self, row, col, text, editable=False, bg_color=None):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        if bg_color:
            item.setBackground(QBrush(QColor(bg_color)))
        
        self.table.setItem(row, col, item)

    def set_block_colors(self, start_row, start_color="#E2EFDA", is_first_block=True):
        self.set_cell(start_row, 0, str((start_row - 2) // 2 + 1), editable=False)
        self.set_cell(start_row, 1, "", editable=True, bg_color=start_color)  # START
        self.set_cell(start_row, 2, "", editable=True, bg_color="#E2EFDA")  # END
        self.set_cell(start_row, 3, "", editable=True, bg_color="#FFF2CC")  # 거리

        # 구간별 평균속도
        if is_first_block:
            self.set_cell(start_row, 4, "0.000", editable=False)
        else:
            self.set_cell(start_row, 4, "", editable=False)
        self.set_cell(start_row + 1, 4, "", editable=False, bg_color="#FCE4D6")  # time 아래 셀을 편집 불가능하게 설정
        self.set_cell(start_row + 1, 5, "", editable=False, bg_color="#FCE4D6")  # vel 아래 셀을 편집 불가능하게 설정

        # 가속도 적용 (구간별 평균속도와 동일하게 설정)
        if is_first_block:
            self.set_cell(start_row, 6, "0.000", editable=False)
        else:
            self.set_cell(start_row, 6, "", editable=False)
        self.set_cell(start_row + 1, 6, "", editable=False, bg_color="#FCE4D6")

        # Acc, Duration
        self.set_cell(start_row, 8, "", editable=True, bg_color="#FCE4D6")
        self.set_cell(start_row, 9, "", editable=True, bg_color="#FCE4D6")

    def add_new_block(self):
        self.data_blocks += 1
        new_rows = self.block_rows
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + new_rows)

        self.add_data_block(self.data_blocks - 1)

        for row in range(current_rows, current_rows + new_rows):
            self.table.setRowHeight(row, 23)

        # 두 번째 블록의 스타일을 복사하여 새 블록에 적용 (내용은 복사하지 않음)
        self.copy_block_style(4, current_rows)

        # 이전 블록의 END 값을 새 록의 START 값으로 설정
        prev_end_item = self.table.item(current_rows - 2, 2)  # 이전 블록의 END 셀
        new_start_item = self.table.item(current_rows, 1)  # 새 블록의 START 셀
        if prev_end_item and new_start_item:
            new_start_item.setText(prev_end_item.text())

        self.update_remove_button()

    def copy_block_style(self, source_row, target_row):
        for col in range(self.total_cols):
            source_item = self.table.item(source_row, col)
            source_item_below = self.table.item(source_row + 1, col)
            
            if source_item:
                self.copy_cell_style(source_item, target_row, col, copy_content=False)
            if source_item_below:
                self.copy_cell_style(source_item_below, target_row + 1, col, copy_content=False)

    def copy_cell_style(self, source_item, target_row, col, copy_content=True):
        new_item = QTableWidgetItem()
        new_item.setBackground(source_item.background())
        new_item.setTextAlignment(source_item.textAlignment())
        new_item.setFlags(source_item.flags())
        
        if copy_content:
            new_item.setText(source_item.text())
        else:
            # 특정 셀에 대해서만 내용을 설정
            if col == 0:  # 구간 번호
                new_item.setText(str((target_row - 2) // 2 + 1))
            elif col in [2, 3, 8, 9]:  # 사용자 입력 셀 (START 제외)
                new_item.setText("")
            elif col == 4 and self.table.rowSpan(target_row, col) == 1:  # 구간별 평균속도 Time ���
                new_item.setText("")
        
        self.table.setItem(target_row, col, new_item)

        # 병합된 셀 처리
        if self.table.rowSpan(source_item.row(), col) > 1:
            self.table.setSpan(target_row, col, self.table.rowSpan(source_item.row(), col), 1)

    def remove_block(self):
        if self.data_blocks > 2:  # 최소 2개의 블록 유지
            self.data_blocks -= 1
            current_rows = self.table.rowCount()
            self.table.setRowCount(current_rows - self.block_rows)
            
            # 구간 번호 업데이트
            self.update_block_numbers()

        self.update_remove_button()

    def update_block_numbers(self):
        for i in range(self.data_blocks):
            row = self.header_rows + i * self.block_rows
            item = self.table.item(row, 0)
            if item:
                item.setText(str(i + 1))

    def update_remove_button(self):
        self.remove_button.setEnabled(self.data_blocks > 2)  # 2개 이상일 때만 활성화

    def update_vel_cell(self, row):
        distance_item = self.table.item(row, 3)
        current_time_item = self.table.item(row + 1, 4)
        vel_item = self.table.item(row + 1, 5)

        if distance_item and current_time_item and vel_item:
            try:
                distance = float(distance_item.text())
                current_time = float(current_time_item.text())
                
                # 이전 블록의 time 값 가져오기
                prev_time = 0
                if row > 2:  # 첫 번째 블록이 아닌 경우
                    prev_time_item = self.table.item(row - 1, 4)
                    if prev_time_item:
                        prev_time = float(prev_time_item.text())
                
                # vel 값 계산
                time_diff = current_time - prev_time
                if time_diff > 0:
                    vel = (distance / time_diff) * 3.6
                    vel_item.setText(f"{vel:.1f}")  # 소수점 첫째 자리까지만 표시
                else:
                    vel_item.setText("0.0")  # 소수점 첫째 자리로 변경
            except ValueError:
                vel_item.setText("0.0")  # 유효하지 않은 입력 처리, 소수점 첫째 자리로 변경

    def update_acc_time_cell(self, row):
        # 구간별 평균속도 time 윗셀과 아랫셀
        avg_time_upper = self.table.item(row, 4)
        avg_time_lower = self.table.item(row + 1, 4)

        # 가속도 적용 time 윗셀과 아랫셀
        acc_time_upper = self.table.item(row, 6)
        acc_time_lower = self.table.item(row + 1, 6)

        if avg_time_upper and avg_time_lower and acc_time_upper and acc_time_lower:
            # 윗셀 복사
            acc_time_upper.setText(avg_time_upper.text())
            acc_time_upper.setBackground(avg_time_upper.background())
            acc_time_upper.setTextAlignment(avg_time_upper.textAlignment())
            acc_time_upper.setFlags(avg_time_upper.flags())

            # 아랫셀 복사
            acc_time_lower.setText(avg_time_lower.text())
            acc_time_lower.setBackground(avg_time_lower.background())
            acc_time_lower.setTextAlignment(avg_time_lower.textAlignment())
            acc_time_lower.setFlags(avg_time_lower.flags())

            # 테이블에 업데이트된 아이템 설정
            self.table.setItem(row, 6, acc_time_upper)
            self.table.setItem(row + 1, 6, acc_time_lower)

    def update_acc_time_cells(self):
        for row in range(2, self.table.rowCount(), 2):
            self.update_acc_time_cell(row)

    def get_table_data(self):
        """현재 표의 데이터를 리스트 형태로 반환"""
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else '')
            table_data.append(row_data)
        return table_data

    def update_from_graph(self, graph_data):
        """그래프로부터 데이터 업데이트"""
        try:
            times = graph_data.get('times', [])
            velocities = graph_data.get('velocities', [])
            
            for i, (time, velocity) in enumerate(zip(times, velocities)):
                row = i * 2 + 1  # 데이터 행 인덱스
                if row < self.table.rowCount():
                    # 시간 업데이트
                    time_item = QTableWidgetItem(f"{time:.3f}")
                    self.table.setItem(row, 4, time_item)
                    
                    # 속도 업데이트
                    vel_item = QTableWidgetItem(f"{velocity:.1f}")
                    self.table.setItem(row, 5, vel_item)
                    
            self.calculate_all_cells()  # 전체 셀 재계산
            
        except Exception as e:
            print(f"그래프 데이터 업데이트 중 오류: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TableWindow()
    window.show()
    sys.exit(app.exec_())
