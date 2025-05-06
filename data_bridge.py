class DataBridge:
    def __init__(self):
        self.table_window = None
        self.graph_window = None
        
    def set_table_window(self, window):
        """테이블 윈도우 연결"""
        self.table_window = window
        
    def set_graph_window(self, window):
        """그래프 윈도우 연결"""
        self.graph_window = window
        
    def update_from_table(self, table_data):
        """표 데이터가 변경되면 그래프 업데이트"""
        if self.graph_window:
            # 표 데이터에서 시간과 속도 추출
            times = []
            velocities = []
            
            for row in range(1, len(table_data), 2):  # 2행씩 처리
                try:
                    time = float(table_data[row][4])    # time 열
                    velocity = float(table_data[row][5]) # velocity 열
                    times.append(time)
                    velocities.append(velocity)
                except (ValueError, IndexError):
                    continue
                    
            self.graph_window.update_graph(times, velocities)
            
    def update_from_graph(self, graph_data):
        """그래프 데이터가 변경되면 표 업데이트"""
        if self.table_window:
            self.table_window.update_from_graph(graph_data)