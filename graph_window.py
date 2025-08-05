"""
GraphWindow - 그래프 윈도우
데이터 시각화 및 인터랙티브 조작
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

from utils.constants import (
    DEFAULT_GRAPH_WIDTH, DEFAULT_GRAPH_HEIGHT,
    OPTIMIZATION_VELOCITY_COLOR, VIDEO_ANALYSIS_VELOCITY_COLOR, GROUND_TRUTH_VELOCITY_COLOR,
    ACCELERATION_VALID_COLOR, ACCELERATION_INVALID_COLOR,
    GRAPH_DPI, POINT_SIZE, LINE_WIDTH,
    DEFAULT_MAX_ACCELERATION, DEFAULT_MAX_DECELERATION
)

class GraphWindow(QMainWindow):
    """그래프 윈도우 클래스"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    data_changed = pyqtSignal(dict)
    
    def __init__(self, data_bridge):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.data_bridge = data_bridge
        
        # 그래프 데이터
        self.optimization_data = []
        self.video_analysis_data = []
        self.ground_truth_data = []
        
        # 인터랙션 상태
        self.dragging = False
        self.selected_point_index = None
        self.graph_visible = True
        
        # UI 초기화
        self._setup_ui()
        self._setup_graph()
        self._connect_signals()
        
        self.logger.info("GraphWindow 초기화 완료")
    
    def _setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("속도 최적화 프로그램 - 그래프")
        self.setGeometry(300, 100, DEFAULT_GRAPH_WIDTH, DEFAULT_GRAPH_HEIGHT)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 그래프 캔버스 먼저 생성
        self.figure = Figure(figsize=(10, 6), dpi=GRAPH_DPI)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 툴바 생성 (캔버스와 함께)
        self.toolbar = NavigationToolbar(self.canvas, self)
        main_layout.addWidget(self.toolbar)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # SHOW GRAPH 버튼
        self.show_graph_button = QPushButton('SHOW GRAPH')
        self.show_graph_button.clicked.connect(self._toggle_graph_visibility)
        button_layout.addWidget(self.show_graph_button)
        
        # Ground Truth 업로드 버튼
        self.upload_csv_button = QPushButton('Ground Truth 업로드')
        self.upload_csv_button.clicked.connect(self._upload_ground_truth)
        button_layout.addWidget(self.upload_csv_button)
        
        # 이미지 저장 버튼들
        self.save_png_button = QPushButton('PNG 저장')
        self.save_png_button.clicked.connect(self._save_as_png)
        button_layout.addWidget(self.save_png_button)
        
        self.save_svg_button = QPushButton('SVG 저장')
        self.save_svg_button.clicked.connect(self._save_as_svg)
        button_layout.addWidget(self.save_svg_button)
        
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        
        # 캔버스를 레이아웃에 추가
        main_layout.addWidget(self.canvas)
    
    def _setup_graph(self):
        """그래프 초기 설정"""
        # Seaborn 스타일 적용
        sns.set_theme(style="darkgrid")
        
        # 그래프 제목 및 레이블
        self.ax.set_title('Interactive Velocity Graph Optimizer', 
                         fontsize=18, fontweight='bold', pad=20)
        self.ax.set_xlabel('TIME (S)', fontsize=12)
        self.ax.set_ylabel('VELOCITY (KM/H)', fontsize=12)
        
        # Y축 범위 설정
        self.ax.set_ylim(0, 50)
        self.ax.yaxis.set_major_locator(plt.MultipleLocator(5))
        
        # 범례 설정
        self.ax.plot([], [], color=ACCELERATION_VALID_COLOR, 
                    label='Acceptable acc/dec range', linewidth=LINE_WIDTH)
        self.ax.plot([], [], color=ACCELERATION_INVALID_COLOR, 
                    label='Unacceptable acc/dec range', linewidth=LINE_WIDTH)
        self.ax.legend()
        
        # 초기 그래프 그리기
        self.canvas.draw()
    
    def _connect_signals(self):
        """시그널 연결"""
        # 마우스 이벤트 연결
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        
        # Data Bridge 시그널 연결
        if self.data_bridge:
            self.data_bridge.graph_data_updated.connect(self._on_data_updated)
            self.data_bridge.error_occurred.connect(self._show_error_message)
    
    # === 그래프 업데이트 메서드 ===
    
    def _on_data_updated(self, graph_data):
        """데이터 업데이트 처리"""
        try:
            self.logger.debug("그래프 데이터 업데이트 시작")
            
            # 데이터 저장
            self.optimization_data = graph_data.get('optimization_velocity', [])
            self.video_analysis_data = graph_data.get('video_analysis_velocity', [])
            self.ground_truth_data = graph_data.get('ground_truth_velocity', [])
            
            # 그래프 다시 그리기
            self._update_graph()
            
            self.logger.debug("그래프 데이터 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"그래프 데이터 업데이트 실패: {e}")
            self._show_error_message("그래프 업데이트 오류", f"그래프 업데이트 중 오류: {e}")
    
    def _update_graph(self):
        """그래프 다시 그리기"""
        if not self.graph_visible:
            return
        
        # 기존 그래프 지우기 (범례 제외)
        lines_to_remove = []
        for line in self.ax.lines:
            if line.get_label() not in ['Acceptable acc/dec range', 'Unacceptable acc/dec range']:
                lines_to_remove.append(line)
        
        for line in lines_to_remove:
            line.remove()
        
        # 새 데이터로 그래프 그리기
        if self.optimization_data:
            times = [point['time'] for point in self.optimization_data]
            velocities = [point['velocity'] for point in self.optimization_data]
            
            # 가속도에 따른 선분 색상 그리기
            settings = self.data_bridge.get_settings() if self.data_bridge else {}
            max_acc = settings.get('max_acceleration', DEFAULT_MAX_ACCELERATION)
            max_dec = settings.get('max_deceleration', DEFAULT_MAX_DECELERATION)
            
            # 각 선분을 가속도에 따라 다른 색상으로 그리기
            for i in range(len(self.optimization_data) - 1):
                curr_point = self.optimization_data[i]
                next_point = self.optimization_data[i + 1]
                
                time_diff = next_point['time'] - curr_point['time']
                if time_diff > 0:
                    # 가속도 계산 (km/h를 m/s로 변환)
                    vel_diff_ms = (next_point['velocity'] - curr_point['velocity']) / 3.6
                    acceleration = vel_diff_ms / time_diff
                    
                    # 가속도 범위에 따른 색상 결정
                    if max_dec <= acceleration <= max_acc:
                        color = ACCELERATION_VALID_COLOR
                    else:
                        color = ACCELERATION_INVALID_COLOR
                else:
                    color = OPTIMIZATION_VELOCITY_COLOR
                
                # 선분 그리기
                self.ax.plot([curr_point['time'], next_point['time']], 
                           [curr_point['velocity'], next_point['velocity']],
                           color=color, linewidth=LINE_WIDTH)
            
            # 포인트 그리기
            self.ax.plot(times, velocities, 
                        color=OPTIMIZATION_VELOCITY_COLOR,
                        marker='o', markersize=POINT_SIZE,
                        linewidth=0, fillstyle='none',
                        label='Optimization Velocity')
            
            # 드래그 중인 포인트 강조
            if self.dragging and self.selected_point_index is not None:
                selected_point = self.optimization_data[self.selected_point_index]
                self.ax.plot(selected_point['time'], selected_point['velocity'],
                            'ro', markersize=POINT_SIZE * 1.5, zorder=10)
        
        if self.video_analysis_data:
            times = [point['time'] for point in self.video_analysis_data]
            velocities = [point['velocity'] for point in self.video_analysis_data]
            
            self.ax.step(times, velocities,
                        color=VIDEO_ANALYSIS_VELOCITY_COLOR,
                        label='Video Analysis Velocity',
                        marker='s', markersize=POINT_SIZE,
                        linewidth=LINE_WIDTH, fillstyle='none',
                        where='post')
        
        if self.ground_truth_data:
            times = [point['time'] for point in self.ground_truth_data]
            velocities = [point['velocity'] for point in self.ground_truth_data]
            
            self.ax.plot(times, velocities,
                        color=GROUND_TRUTH_VELOCITY_COLOR,
                        label='Ground Truth Velocity',
                        linestyle='--', linewidth=LINE_WIDTH)
        
        # 범례 업데이트
        self.ax.legend()
        
        # 캔버스 다시 그리기
        self.canvas.draw()
    
    # === 마우스 이벤트 핸들러 ===
    
    def _on_mouse_press(self, event):
        """마우스 클릭 이벤트"""
        if event.inaxes != self.ax or not self.graph_visible:
            return
        
        # 최적화 속도 데이터가 있는지 확인
        if not self.optimization_data:
            return
        
        # 클릭 위치에서 가장 가까운 포인트 찾기
        click_x, click_y = event.xdata, event.ydata
        min_distance = float('inf')
        closest_index = None
        
        for i, point in enumerate(self.optimization_data):
            # 거리 계산 (x축은 시간 단위, y축은 속도 단위로 정규화)
            x_dist = (point['time'] - click_x) * 10  # 시간축 가중치
            y_dist = (point['velocity'] - click_y)   # 속도축
            distance = (x_dist**2 + y_dist**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        # 임계값 내에 있으면 드래그 시작
        threshold = 5.0  # 클릭 감지 임계값
        if min_distance < threshold and closest_index is not None:
            self.dragging = True
            self.selected_point_index = closest_index
            self.logger.debug(f"포인트 {closest_index} 선택됨: {self.optimization_data[closest_index]}")
    
    def _on_mouse_release(self, event):
        """마우스 릴리즈 이벤트"""
        if self.dragging:
            self.dragging = False
            
            # 변경된 데이터를 Data Bridge로 전송
            if self.data_bridge:
                graph_data = {
                    'optimization_velocity': self.optimization_data
                }
                self.data_bridge.update_from_graph(graph_data)
                self.logger.debug("드래그 완료 - 데이터 업데이트 전송")
            
            self.selected_point_index = None
    
    def _on_mouse_motion(self, event):
        """마우스 이동 이벤트"""
        if self.dragging and event.inaxes == self.ax and self.selected_point_index is not None:
            # 새로운 Y 좌표 (속도값)으로 업데이트
            new_velocity = max(0, event.ydata)  # 속도는 0 이상
            
            # 가속도 제한 검증
            if self._validate_velocity_change(self.selected_point_index, new_velocity):
                # 선택된 포인트의 속도 업데이트
                self.optimization_data[self.selected_point_index]['velocity'] = new_velocity
                
                # 연결된 포인트들도 업데이트 (같은 시간대의 포인트)
                current_time = self.optimization_data[self.selected_point_index]['time']
                for i, point in enumerate(self.optimization_data):
                    if abs(point['time'] - current_time) < 0.001 and i != self.selected_point_index:
                        point['velocity'] = new_velocity
                
                # 그래프 실시간 업데이트
                self._update_graph()
                self.logger.debug(f"포인트 {self.selected_point_index} 속도 변경: {new_velocity:.2f} km/h")
    
    # === 버튼 이벤트 핸들러 ===
    
    def _toggle_graph_visibility(self):
        """그래프 표시/숨김 토글"""
        self.graph_visible = not self.graph_visible
        
        if self.graph_visible:
            self._update_graph()
            self.show_graph_button.setText('HIDE GRAPH')
        else:
            # 모든 라인 숨기기
            for line in self.ax.lines:
                line.set_visible(False)
            self.canvas.draw()
            self.show_graph_button.setText('SHOW GRAPH')
        
        self.logger.info(f"그래프 표시 상태: {self.graph_visible}")
    
    def _upload_ground_truth(self):
        """Ground Truth CSV 업로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ground Truth CSV 선택", "", "CSV files (*.csv)"
        )
        
        if file_path:
            if self.data_bridge:
                success = self.data_bridge.load_ground_truth_csv(file_path)
                if success:
                    self._show_info_message("파일 로드", "Ground Truth 파일을 성공적으로 로드했습니다.")
                else:
                    self._show_error_message("파일 로드 오류", "Ground Truth 파일 로드에 실패했습니다.")
    
    def _save_as_png(self):
        """PNG 이미지로 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PNG 파일로 저장", "", "PNG files (*.png)"
        )
        
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                self._show_info_message("이미지 저장", f"PNG 파일로 저장했습니다:\n{file_path}")
                self.logger.info(f"PNG 저장 완료: {file_path}")
            except Exception as e:
                self.logger.error(f"PNG 저장 실패: {e}")
                self._show_error_message("저장 오류", f"PNG 저장 중 오류: {e}")
    
    def _save_as_svg(self):
        """SVG 이미지로 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "SVG 파일로 저장", "", "SVG files (*.svg)"
        )
        
        if file_path:
            try:
                self.figure.savefig(file_path, format='svg', bbox_inches='tight')
                self._show_info_message("이미지 저장", f"SVG 파일로 저장했습니다:\n{file_path}")
                self.logger.info(f"SVG 저장 완료: {file_path}")
            except Exception as e:
                self.logger.error(f"SVG 저장 실패: {e}")
                self._show_error_message("저장 오류", f"SVG 저장 중 오류: {e}")
    
    # === 유틸리티 메서드 ===
    
    def _validate_velocity_change(self, point_index, new_velocity):
        """속도 변경 시 가속도 제한 검증"""
        try:
            # 인접 포인트들과의 가속도 계산
            settings = self.data_bridge.get_settings() if self.data_bridge else {}
            max_acc = settings.get('max_acceleration', DEFAULT_MAX_ACCELERATION)
            max_dec = settings.get('max_deceleration', DEFAULT_MAX_DECELERATION)
            
            # 이전 포인트와의 가속도 검증
            if point_index > 0:
                prev_point = self.optimization_data[point_index - 1]
                time_diff = self.optimization_data[point_index]['time'] - prev_point['time']
                
                if time_diff > 0:
                    # km/h를 m/s로 변환하여 가속도 계산
                    vel_diff_ms = (new_velocity - prev_point['velocity']) / 3.6
                    acceleration = vel_diff_ms / time_diff
                    
                    if acceleration > max_acc or acceleration < max_dec:
                        self.logger.debug(f"가속도 제한 초과: {acceleration:.2f} m/s²")
                        return False
            
            # 다음 포인트와의 가속도 검증
            if point_index < len(self.optimization_data) - 1:
                next_point = self.optimization_data[point_index + 1]
                time_diff = next_point['time'] - self.optimization_data[point_index]['time']
                
                if time_diff > 0:
                    # km/h를 m/s로 변환하여 가속도 계산
                    vel_diff_ms = (next_point['velocity'] - new_velocity) / 3.6
                    acceleration = vel_diff_ms / time_diff
                    
                    if acceleration > max_acc or acceleration < max_dec:
                        self.logger.debug(f"가속도 제한 초과: {acceleration:.2f} m/s²")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"속도 검증 실패: {e}")
            return True  # 에러 시 허용
    
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