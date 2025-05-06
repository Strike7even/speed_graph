import sys
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

class GraphWindow(QMainWindow):
    # 가속도 임계값 설정
    ACCELERATION_THRESHOLD = 3.5
    DECELERATION_THRESHOLD = -7.85
    
    def __init__(self, data_bridge=None):
        super().__init__()
        self.data_bridge = data_bridge
        self.setWindowTitle('속도 그래프')
        self.setGeometry(300, 100, 1000, 600)
        
        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 그래프 설정
        self.fig = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        # 툴바 추가
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Show Graph 버튼 추가
        self.show_graph_button = QPushButton('SHOW GRAPH')
        self.show_graph_button.clicked.connect(self.toggle_visibility)
        
        # 레이아웃에 위젯 추가
        layout.addWidget(self.toolbar)
        layout.addWidget(self.show_graph_button)
        layout.addWidget(self.canvas)
        
        # 초기 그래프 설정
        self.setup_graph_style()
        self.draggable_point = None

    def toggle_visibility(self):
        """SHOW GRAPH 버튼 콜백"""
        lines = self.ax.get_lines()
        if lines:
            lines[0].set_visible(not lines[0].get_visible())
            self.canvas.draw_idle()

    def setup_graph_style(self):
        """그래프 기본 스타일 설정"""
        sns.set_theme(style="darkgrid")
        self.ax.set_title('Interactive Velocity Graph Optimizer', fontsize=18, fontweight='bold', pad=20)
        self.ax.set_xlabel('TIME (S)', fontsize=12)
        self.ax.set_ylabel('VELOCITY (KM/H)', fontsize=12)
        
        # Y축 범위 및 눈금 설정
        self.ax.set_ylim(0, 50)  # y_max는 데이터에 따라 조정
        self.ax.yaxis.set_major_locator(plt.MultipleLocator(5))
        
        # 범례 추가
        self.ax.plot([], [], color='green', label='Acceptable acc/dec range')
        self.ax.plot([], [], color='red', label='Unacceptable acc/dec range')
        self.ax.legend()
        
    def get_color(self, acceleration):
        """가속도에 따른 색상 결정"""
        if self.DECELERATION_THRESHOLD <= acceleration <= self.ACCELERATION_THRESHOLD:
            return 'green'
        return 'red'

    def update_graph(self, times, velocities):
        """표로부터 받은 데이터로 그래프 업데이트"""
        try:
            self.ax.clear()
            self.setup_graph_style()
            
            if times and velocities:
                # 분석 속도 (실선)
                line1, = self.ax.plot(times, velocities, 
                                    label='Optimization Velocity',
                                    marker='o', 
                                    fillstyle='none',
                                    markersize=8)
                
                # 실제 속도 (계단 형식)
                if len(times) > 1:
                    self.ax.step(times, velocities,
                            where='post',
                            label='Video Analysis Velocity',
                            marker='s',
                            fillstyle='none',
                            markersize=8)
                
                # 주석 추가
                annotations = []
                for x, y in zip(times, velocities):
                    annotation = self.ax.annotate(
                        f'{y:.1f}', (x, y),
                        textcoords="offset points",
                        xytext=(0, 15),
                        ha='center',
                        fontsize=8
                    )
                    annotations.append(annotation)
                
                # 드래그 기능 추가
                self.draggable_point = self.DraggablePoint(line1, annotations, self.ax, self)
                self.draggable_point.connect()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"그래프 업데이트 중 오류: {e}")

    class DraggablePoint:
        def __init__(self, line, annotations, ax, parent):
            self.line = line
            self.press = None
            self.selected_index = None
            self.annotations = annotations
            self.ax = ax
            self.parent = parent
            self.segment_lines = []

        def connect(self):
            self.cidpress = self.line.figure.canvas.mpl_connect(
                'button_press_event', self.on_press)
            self.cidrelease = self.line.figure.canvas.mpl_connect(
                'button_release_event', self.on_release)
            self.cidmotion = self.line.figure.canvas.mpl_connect(
                'motion_notify_event', self.on_motion)

        def on_press(self, event):
            if event.inaxes != self.line.axes:
                return
            contains, _ = self.line.contains(event)
            if not contains:
                return
            self.selected_index = self.get_nearest_index(event)
            if self.selected_index is not None and self.selected_index % 2 == 0:
                self.press = event.xdata, event.ydata

        def get_nearest_index(self, event):
            xdata = self.line.get_xdata()
            ydata = self.line.get_ydata()
            distances = np.sqrt((xdata - event.xdata) ** 2 + (ydata - event.ydata) ** 2)
            min_distance = np.min(distances)
            if min_distance < 0.5:
                return np.argmin(distances)
            return None
        
        def on_motion(self, event):
            if self.press is None or self.selected_index is None:
                return
            if event.inaxes != self.line.axes:
                return
            
            new_y = round(event.ydata * 10) / 10
            ydata = self.line.get_ydata()
            xdata = self.line.get_xdata()
            
            ydata[self.selected_index] = new_y
            
            # 이전 점들 업데이트
            for i in range(self.selected_index - 2, -1, -2):
                if i + 1 < len(ydata):
                    slope = (ydata[i+2] - ydata[i+1]) / (xdata[i+2] - xdata[i+1])
                    ydata[i] = ydata[i+1] - slope * (xdata[i+1] - xdata[i])
            
            # 이후 점들 업데이트
            for i in range(self.selected_index + 2, len(ydata), 2):
                if i - 2 >= 0:
                    slope = (ydata[i-1] - ydata[i-2]) / (xdata[i-1] - xdata[i-2])
                    ydata[i] = ydata[i-1] + slope * (xdata[i] - xdata[i-1])

            # 가속도 선 업데이트
            for line in self.segment_lines:
                line.remove()
            self.segment_lines.clear()

            for i in range(len(xdata) - 1):
                x1, x2 = xdata[i], xdata[i+1]
                y1, y2 = ydata[i], ydata[i+1]
                acceleration = (y2 - y1) / (x2 - x1)
                color = self.parent.get_color(acceleration)
                line, = self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=2)
                self.segment_lines.append(line)

            self.line.set_ydata(ydata)

            # 주석 업데이트
            for i, annotation in enumerate(self.annotations):
                annotation.set_text(f'{ydata[i]:.1f}')
                annotation.xy = (xdata[i], ydata[i])
                annotation.xyann = (0, 15)

            self.line.figure.canvas.draw_idle()
            
            # 데이터 브릿지 업데이트
            if self.parent.data_bridge:
                graph_data = {
                    'times': xdata.tolist(),
                    'velocities': ydata.tolist()
                }
                self.parent.data_bridge.update_from_graph(graph_data)

        def on_release(self, event):
            self.press = None
            self.selected_index = None
            self.line.figure.canvas.draw()

        def disconnect(self):
            self.line.figure.canvas.mpl_disconnect(self.cidpress)
            self.line.figure.canvas.mpl_disconnect(self.cidrelease)
            self.line.figure.canvas.mpl_disconnect(self.cidmotion)
