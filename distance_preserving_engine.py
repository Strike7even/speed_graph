"""
거리보존 속도 최적화 엔진
앵커 노드 기반 실시간 드래그 최적화

수학적 기반:
- 거리보존: (v_i + v_{i+1}) * Δt_i / 2 = s_i  
- 선형전파: v_i = A_i * w + B_i
- 앵커노드: w = v_k (단일 자유도)
"""

from typing import List, Dict, Optional


class DistancePreservingEngine:
    """거리보존 속도 최적화 엔진
    
    핵심 원리:
    1. 거리보존: 각 구간의 사다리꼴 면적 = 원래 거리
    2. 앵커노드: 하나의 노드 속도로 전체 프로파일 제어  
    3. 선형전파: v_i = A_i * w + B_i (O(N) 실시간 업데이트)
    """
    
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        
        # 사전계산 배열 (O(N) 메모리)
        self.t: List[float] = []       # 노드 시간 [t_0, t_1, ..., t_N]
        self.dt: List[float] = []      # 구간 간격 [Δt_0, ..., Δt_{N-1}]  
        self.m: List[float] = []       # 거리계수 [m_0, ..., m_{N-1}]
        self.A: List[int] = []         # 전파방향 [A_0, ..., A_N]
        self.B: List[float] = []       # 오프셋 [B_0, ..., B_N]
        
        # 상태 관리
        self.anchor_k: int = -1        # 앵커 노드 인덱스
        self.w_prev: float = 0.0       # 이전 앵커 속도 (m/s)
        self.is_prepared: bool = False
        
    def prepare_initial_graph(self, segments: List[Dict]) -> List[Dict]:
        """초기 그래프 생성 (정지 상태)
        
        Args:
            segments: [{'frame_start', 'frame_end', 'distance'}]
            
        Returns:
            노드 기반 속도 프로파일 [{'time', 'velocity'}]
        """
        try:
            
            # 입력 검증
            self._validate_segments(segments)
            
            N = len(segments)  # 구간 수
            
            # 1. 시간 노드 및 구간 간격 계산
            self.t = [0.0]
            self.dt = []
            
            for i, seg in enumerate(segments):
                frame_start = float(seg['frame_start'])
                frame_end = float(seg['frame_end'])
                
                dt_i = (frame_end - frame_start) / self.fps
                self.dt.append(dt_i)
                self.t.append(self.t[-1] + dt_i)
            
            # 2. 거리계수 계산 (m_i = 2*s_i/dt_i)
            self.m = []
            for i, seg in enumerate(segments):
                distance = float(seg['distance'])
                m_i = 2.0 * distance / self.dt[i]  # m/s
                self.m.append(m_i)
            
            # 3. 앵커 노드 선택 (중간 노드)
            self.anchor_k = N // 2
            
            # 4. 전파방향 계수 (A_i = 1 for anchor, (-1)^(i-k) for others)
            self.A = []
            for i in range(N + 1):
                if i == self.anchor_k:
                    # 앵커 노드는 항상 1 (드래그 방향과 일치)
                    A_i = 1
                else:
                    # 다른 노드들은 (-1)^(i-k) 공식 적용
                    distance_from_anchor = i - self.anchor_k
                    A_i = 1 if (distance_from_anchor % 2) == 0 else -1
                self.A.append(A_i)
            
            # 5. 오프셋 계수 계산 (B_i)
            self.B = [0.0] * (N + 1)
            self.B[self.anchor_k] = 0.0
            
            # 앵커에서 오른쪽으로 전파
            for i in range(self.anchor_k, N):
                self.B[i + 1] = self.m[i] - self.B[i]
                
            # 앵커에서 왼쪽으로 전파  
            for i in range(self.anchor_k, 0, -1):
                self.B[i - 1] = self.m[i - 1] - self.B[i]
            
            # 6. 초기 앵커 속도 설정 (w = m[0]/2)
            self.w_prev = self.m[0] / 2  # m/s
            
            # 7. 초기 속도 프로파일 생성
            v_mps = [self.A[i] * self.w_prev + self.B[i] for i in range(N + 1)]
            
            # 8. km/h 변환 및 포인트 생성
            points = []
            for i in range(N + 1):
                points.append({
                    'time': self.t[i],
                    'velocity': v_mps[i] * 3.6  # m/s → km/h
                })
            
            self.is_prepared = True
            
            # 거리보존 검증
            self._verify_distance_conservation(points)
            
            return points
            
        except Exception as e:
            raise
    
    def begin_drag(self, anchor_index: int) -> bool:
        """드래그 시작 - A/B 계수 캐시
        
        Args:
            anchor_index: UI에서 선택한 노드 인덱스
            
        Returns:
            준비 성공 여부
        """
        try:
            if not self.is_prepared:
                return False
                
            # 앵커 인덱스 유효성 검사
            if anchor_index < 0 or anchor_index >= len(self.A):
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def update_realtime(self, new_anchor_velocity_kmh: float, 
                       method: str = "direct") -> List[Dict]:
        """실시간 속도 프로파일 업데이트
        
        Args:
            new_anchor_velocity_kmh: 새로운 앵커 속도 (km/h)
            method: "direct" (직접식) 또는 "delta" (델타식)
            
        Returns:
            업데이트된 속도 프로파일 [{'time', 'velocity'}]
        """
        try:
            if not self.is_prepared:
                return []
            
            if method == "direct":
                return self._update_direct(new_anchor_velocity_kmh)
            elif method == "delta":
                return self._update_delta(new_anchor_velocity_kmh)
            else:
                return []
                
        except Exception as e:
            return []
    
    def _update_direct(self, new_anchor_velocity_kmh: float) -> List[Dict]:
        """직접식 업데이트: v = [A[i]*w + B[i] for i in range(N+1)]"""
        w = new_anchor_velocity_kmh / 3.6  # km/h → m/s
        
        # 전체 속도 계산 (O(N))
        points = []
        for i in range(len(self.t)):
            v_i_ms = self.A[i] * w + self.B[i]
            v_i_kmh = max(0, v_i_ms * 3.6)  # 음수 속도 방지
            
            points.append({
                'time': self.t[i],
                'velocity': v_i_kmh
            })
        
        self.w_prev = w
        return points
    
    def _update_delta(self, new_anchor_velocity_kmh: float) -> List[Dict]:
        """델타식 업데이트: dv[i] = A[i] * dw (미세히 더 빠름)"""
        w = new_anchor_velocity_kmh / 3.6  # km/h → m/s
        dw = w - self.w_prev  # 변화량
        
        if abs(dw) < 1e-6:  # 변화 없음
            return []
        
        # 이전 속도에서 변화량만 더함
        points = []
        for i in range(len(self.t)):
            # 이전 속도 복원 (역계산)
            prev_v_ms = self.A[i] * self.w_prev + self.B[i]
            # 변화량 적용
            new_v_ms = prev_v_ms + self.A[i] * dw
            new_v_kmh = max(0, new_v_ms * 3.6)
            
            points.append({
                'time': self.t[i],
                'velocity': new_v_kmh
            })
        
        self.w_prev = w
        return points
    
    def _validate_segments(self, segments: List[Dict]) -> None:
        """세그먼트 데이터 검증"""
        if not segments:
            raise ValueError("빈 세그먼트 데이터")
        
        for i, seg in enumerate(segments):
            # 필수 필드 확인
            required_fields = ['frame_start', 'frame_end', 'distance']
            for field in required_fields:
                if field not in seg:
                    raise ValueError(f"구간 {i+1}: '{field}' 필드 누락")
            
            # 수치 변환 및 검증
            try:
                frame_start = float(seg['frame_start'])
                frame_end = float(seg['frame_end'])
                distance = float(seg['distance'])
            except (ValueError, TypeError):
                raise ValueError(f"구간 {i+1}: 수치 데이터 오류")
            
            # 논리적 검증
            if frame_end <= frame_start:
                raise ValueError(f"구간 {i+1}: frame_end > frame_start 이어야 함")
            
            if distance <= 0:
                raise ValueError(f"구간 {i+1}: 거리는 양수여야 함 (현재: {distance})")
            
            if self.fps <= 0:
                raise ValueError(f"FPS는 양수여야 함 (현재: {self.fps})")
            
            # 시간 간격 검증
            dt = (frame_end - frame_start) / self.fps
            if dt <= 0:
                raise ValueError(f"구간 {i+1}: 시간 간격이 0 이하 (dt: {dt})")
    
    def _verify_distance_conservation(self, velocity_profile: List[Dict]) -> bool:
        """거리보존 검증
        
        Args:
            velocity_profile: 속도 프로파일
            
        Returns:
            검증 성공 여부
        """
        try:
            
            for i in range(len(self.dt)):
                # 구간 i의 실제 거리 계산 (사다리꼴 적분)
                v_start = velocity_profile[i]['velocity'] / 3.6  # km/h → m/s
                v_end = velocity_profile[i + 1]['velocity'] / 3.6
                
                calculated_distance = (v_start + v_end) * self.dt[i] / 2
                expected_distance = self.m[i] * self.dt[i] / 2
                
                error = abs(calculated_distance - expected_distance)
                
                if error > 1e-9:  # 1나노미터 오차 허용
                    return False
            return True
            
        except Exception as e:
            return False
    
    def get_anchor_index(self) -> int:
        """앵커 노드 인덱스 반환"""
        return self.anchor_k
    
    def is_ready(self) -> bool:
        """준비 상태 확인"""
        return self.is_prepared
    
    def reset(self) -> None:
        """상태 초기화"""
        self.t.clear()
        self.dt.clear()
        self.m.clear()
        self.A.clear()
        self.B.clear()
        self.anchor_k = -1
        self.w_prev = 0.0
        self.is_prepared = False