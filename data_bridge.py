"""
DataBridge - 데이터 통신 허브
모든 모듈 간 데이터 실시간 동기화 및 통신 중재
"""

import json
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

from utils.constants import (
    DEFAULT_MAX_ACCELERATION, DEFAULT_MAX_DECELERATION,
    DEFAULT_SEGMENTS, DEFAULT_FPS, DEFAULT_UNIFORM_MOTION_THRESHOLD
)

class DataBridge(QObject):
    """데이터 통신 허브 클래스"""
    
    # 시그널 정의
    data_changed = pyqtSignal(dict)  # 데이터 변경 시그널
    table_data_updated = pyqtSignal(dict)  # 테이블 데이터 업데이트
    graph_data_updated = pyqtSignal(dict)  # 그래프 데이터 업데이트
    error_occurred = pyqtSignal(str)  # 에러 발생 시그널
    
    def __init__(self):
        super().__init__()
        
        # 연결된 윈도우 참조
        self.table_window = None
        self.graph_window = None
        
        # 데이터 저장소
        self._project_data = self._initialize_project_data()
        self._unsaved_changes = False
        
        # 앵커 기반 선형식 시스템
        self._linear_coefficients = None  # 거리 제약 상수들 (m_i)
        self._linear_params = None        # A_i, B_i 계수들
        self._anchor_index = 0           # 앵커 포인트 인덱스
        self._current_anchor_velocity = None  # 현재 앵커 속도값
        

    
    def _initialize_project_data(self) -> Dict[str, Any]:
        """프로젝트 데이터 초기화"""
        return {
            'project_info': {
                'name': '',
                'created_date': '',
                'modified_date': ''
            },
            'settings': {
                'max_acceleration': DEFAULT_MAX_ACCELERATION,
                'max_deceleration': DEFAULT_MAX_DECELERATION,
                'fps': DEFAULT_FPS
            },
            'segments': self._create_default_segments(),
            'graph_data': {
                'optimization_velocity': [],
                'video_analysis_velocity': [],
                'ground_truth_velocity': []
            },
            'ground_truth_file': None
        }
    
    def _create_default_segments(self) -> List[Dict[str, Any]]:
        """기본 구간 데이터 생성"""
        segments = []
        for i in range(DEFAULT_SEGMENTS):
            segment = {
                'segment_num': i + 1,
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
            segments.append(segment)
        return segments
    
    def set_windows(self, table_window, graph_window):
        """윈도우 참조 설정"""
        self.table_window = table_window
        self.graph_window = graph_window

    
    # === 데이터 동기화 메서드 ===
    
    def update_from_table(self, table_data: Dict[str, Any]):
        """테이블에서 데이터 업데이트"""
        try:

            
            # 세그먼트 데이터 업데이트
            if 'segments' in table_data:
                segments = table_data['segments']

                for i, segment in enumerate(segments):
                    pass

                self._project_data['segments'] = table_data['segments']
            
            # 설정 데이터 업데이트
            if 'settings' in table_data:
                self._project_data['settings'].update(table_data['settings'])
            
            # 그래프 데이터 계산 및 업데이트
            self._calculate_graph_data()
            
            # 변경사항 플래그 설정
            self._unsaved_changes = True
            
            # 그래프 윈도우에 업데이트 알림
            self.graph_data_updated.emit(self._project_data['graph_data'])
            

            
        except Exception as e:
            pass
            self.error_occurred.emit(f"테이블 데이터 업데이트 중 오류: {e}")
    
    def update_from_graph(self, graph_data: Dict[str, Any]):
        """그래프에서 데이터 업데이트 - 앵커 시스템 적용"""
        try:
            # 최적화 속도 데이터 업데이트
            if 'optimization_velocity' in graph_data:
                self._project_data['graph_data']['optimization_velocity'] = graph_data['optimization_velocity']
                
                # 앵커 시스템이 초기화된 경우, 첫 번째 포인트를 기준으로 앵커 속도 추출
                if (self._linear_coefficients and self._linear_params and 
                    graph_data['optimization_velocity']):
                    first_point = graph_data['optimization_velocity'][0]
                    self._current_anchor_velocity = first_point['velocity']
            
            # 테이블 데이터 역산 및 업데이트
            self._update_table_from_optimization_data()
            
            # 변경사항 플래그 설정
            self._unsaved_changes = True
            
            # 테이블 윈도우에 업데이트 알림 - graph_updated 플래그 추가하여 순환 방지
            self.table_data_updated.emit({'segments': self._project_data['segments'], 'graph_updated': True})
            

            
        except Exception as e:
            pass
            self.error_occurred.emit(f"그래프 데이터 업데이트 중 오류: {e}")
    
    def _calculate_graph_data(self):
        """테이블 데이터를 기반으로 그래프 데이터 계산"""
        try:
            # 기존 최적화 속도 데이터 초기화
            optimization_velocity = []
            video_analysis_velocity = []
            
            current_time = 0.0
            fps = self._project_data['settings']['fps']
            
            segments = self._project_data['segments']

            
            for i, segment in enumerate(segments):
                # 구간 데이터 추출
                frame_start = self._parse_float(segment.get('frame_start', 0))
                frame_end = self._parse_float(segment.get('frame_end', 0))
                distance = self._parse_float(segment.get('distance', 0))
                avg_time = self._parse_float(segment.get('avg_time', 0))
                avg_velocity = self._parse_float(segment.get('avg_velocity', 0))
                


                acc_time = self._parse_float(segment.get('acc_time', 0))
                acc_velocity = self._parse_float(segment.get('acc_velocity', 0))
                acceleration = self._parse_float(segment.get('acceleration', 0))
                duration = self._parse_float(segment.get('duration', 0))
                
                # 세그먼트 시간 정보 계산
                if frame_start > 0 and frame_end > 0 and fps > 0:
                    segment_duration = (frame_end - frame_start) / fps
                    avg_velocity_ms = avg_velocity / 3.6 if avg_velocity > 0 else 0  # km/h → m/s
                    

                    
                    # Video Analysis 데이터 (계단식)
                    if avg_velocity > 0:
                        point1 = {'time': current_time, 'velocity': avg_velocity}
                        point2 = {'time': current_time + segment_duration, 'velocity': avg_velocity}
                        
                        video_analysis_velocity.append(point1)
                        video_analysis_velocity.append(point2)
                        

                    else:
                        pass
                    
                    current_time += segment_duration
            
            # Optimization 데이터 생성 (노드-선형식 알고리즘)
            optimization_velocity = self._generate_optimization_velocity(segments, fps)
            
            # 그래프 데이터 업데이트
            self._project_data['graph_data']['optimization_velocity'] = optimization_velocity
            self._project_data['graph_data']['video_analysis_velocity'] = video_analysis_velocity
            
            # 테이블에서 계산된 값들 업데이트 (duration, avg_velocity 등)
            self._update_calculated_values()
            
            # 최적화 데이터가 생성되었으므로 가속도 값들 계산
            if optimization_velocity:
                self._update_table_from_optimization_data()
            



            
        except Exception as e:
            pass
            self.error_occurred.emit(f"그래프 데이터 계산 중 오류: {e}")
    
    def _initialize_linear_coefficients(self, segments, fps):
        """거리 제약 기반 선형 계수 초기화"""
        try:
            coefficients = []
            
            for i, segment in enumerate(segments):
                # 구간 데이터 추출
                frame_start = self._parse_float(segment.get('frame_start', 0))
                frame_end = self._parse_float(segment.get('frame_end', 0))
                distance = self._parse_float(segment.get('distance', 0))
                
                if frame_start > 0 and frame_end > 0 and fps > 0 and distance > 0:
                    # 구간 시간 계산
                    duration = (frame_end - frame_start) / fps
                    
                    # m_i = 2s_i / Δt_i 계산 (거리 제약 상수)
                    # distance(m) → km/h 변환: m/s * 3.6
                    m_i = 2 * distance * 3.6 / duration if duration > 0 else 0
                    
                    coefficients.append({
                        'segment_index': i,
                        'distance_constraint': m_i,  # m_i 상수
                        'duration': duration,
                        'distance': distance,
                        'start_time': 0  # 나중에 계산
                    })
                else:
                    # 유효하지 않은 구간은 기본값
                    coefficients.append({
                        'segment_index': i,
                        'distance_constraint': 0,
                        'duration': 0,
                        'distance': 0,
                        'start_time': 0
                    })
            
            # 시작 시간 계산
            current_time = 0.0
            for coeff in coefficients:
                coeff['start_time'] = current_time
                current_time += coeff['duration']
            
            return coefficients
            
        except Exception as e:
            return []
    
    def _calculate_linear_coefficients(self, coefficients, anchor_index=0):
        """앵커 기반 A_i, B_i 계수 계산 - 올바른 m-전파식 사용"""
        try:
            if not coefficients:
                return []
            
            num_segments = len(coefficients)
            linear_params = [{'A': 0.0, 'B': 0.0} for _ in range(num_segments)]
            
            # 1. A 계수 설정 (부호 패턴)
            for i in range(num_segments):
                distance_from_anchor = abs(i - anchor_index)
                if distance_from_anchor % 2 == 0:
                    linear_params[i]['A'] = 1.0  # 앵커와 같은 방향
                else:
                    linear_params[i]['A'] = -1.0  # 앵커와 반대 방향
            
            # 2. B 계수 전파식 적용: B[i+1] = m[i] - B[i]
            # 앵커부터 시작
            linear_params[anchor_index]['B'] = 0.0
            
            # 앵커에서 앞으로 전파 (anchor_index → N-1)
            for i in range(anchor_index, num_segments - 1):
                m_i = coefficients[i]['distance_constraint']
                linear_params[i + 1]['B'] = m_i - linear_params[i]['B']
            
            # 앵커에서 뒤로 전파 (anchor_index → 0)
            for i in range(anchor_index, 0, -1):
                m_i_minus_1 = coefficients[i - 1]['distance_constraint']
                linear_params[i - 1]['B'] = m_i_minus_1 - linear_params[i]['B']
            
            return linear_params
            
        except Exception as e:
            return []
    
    def _determine_initial_anchor(self, segments):
        """초기 앵커 속도 결정"""
        try:
            # 첫 번째 구간의 평균 속도를 기준으로 설정
            if segments and len(segments) > 0:
                first_segment = segments[0]
                avg_velocity = self._parse_float(first_segment.get('avg_velocity', 0))
                return avg_velocity * 0.8 if avg_velocity > 0 else 50.0  # 기본값 50km/h
            return 50.0
            
        except Exception as e:
            return 50.0
    
    def _generate_optimization_velocity(self, segments, fps):
        """앵커 기반 노드-선형식 알고리즘: 거리 보존과 연속성 완벽 보장"""
        try:
            # 1. 거리 제약 상수 계산
            self._linear_coefficients = self._initialize_linear_coefficients(segments, fps)
            
            if not self._linear_coefficients:
                return []
            
            # 2. 선형 계수 계산 (앵커는 첫 번째 구간으로 설정)
            self._anchor_index = 0
            self._linear_params = self._calculate_linear_coefficients(
                self._linear_coefficients, self._anchor_index
            )
            
            # 3. 초기 앵커 속도 결정
            if self._current_anchor_velocity is None:
                self._current_anchor_velocity = self._determine_initial_anchor(segments)
            
            # 4. 앵커 기반으로 모든 포인트 생성
            optimization_velocity = []
            
            print(f"[DataBridge] 앵커 속도: {self._current_anchor_velocity:.2f} km/h")
            
            # B 계수 전파식 검증
            print("[DataBridge] === B 계수 전파식 검증 ===")
            for i in range(len(self._linear_params)):
                B_i = self._linear_params[i]['B']
                print(f"[DataBridge] B[{i}] = {B_i:.2f}")
            
            # 전파 관계 검증: B[i] + B[i+1] = m[i]
            for i in range(len(self._linear_coefficients)-1):
                B_current = self._linear_params[i]['B']
                B_next = self._linear_params[i+1]['B']
                m_i = self._linear_coefficients[i]['distance_constraint']
                
                expected = m_i
                actual = B_current + B_next
                diff = abs(expected - actual)
                
                print(f"[DataBridge] 검증 구간{i+1}: B[{i}]({B_current:.2f}) + B[{i+1}]({B_next:.2f}) = {actual:.2f} vs m[{i}] = {expected:.2f}, 차이: {diff:.6f}")
                if diff > 1e-6:
                    print(f"[DataBridge] ❌ 전파식 오류 발견: 구간{i+1}")
                else:
                    print(f"[DataBridge] ✅ 전파식 정상: 구간{i+1}")
            print("[DataBridge] === B 계수 검증 완료 ===")
            
            for i, (coeff, param) in enumerate(zip(self._linear_coefficients, self._linear_params)):
                if coeff['duration'] <= 0:
                    continue
                
                # 시작 속도: v_i(w) = A_i * w + B_i
                start_velocity = param['A'] * self._current_anchor_velocity + param['B']
                
                # 끝 속도: 거리 제약 적용 v_i+1 = m_i - v_i
                end_velocity = coeff['distance_constraint'] - start_velocity
                
                print(f"[DataBridge] 구간{i+1}: A={param['A']:+.1f}, B={param['B']:+.2f}, m={coeff['distance_constraint']:.2f}")
                print(f"[DataBridge] 구간{i+1}: 시작={start_velocity:.2f}, 끝={end_velocity:.2f} km/h")
                
                # 포인트 생성
                start_time = coeff['start_time']
                end_time = start_time + coeff['duration']
                
                optimization_velocity.extend([
                    {'time': start_time, 'velocity': start_velocity},
                    {'time': end_time, 'velocity': end_velocity}
                ])
            
            # 노드 인덱스 매핑 검사
            print("[DataBridge] === 노드 인덱스 매핑 검사 ===")
            for i in range(len(optimization_velocity)):
                if i % 2 == 0:  # 시작 포인트
                    segment_num = (i // 2) + 1
                    print(f"[DataBridge] 노드[{i}] = 구간{segment_num} 시작: {optimization_velocity[i]['velocity']:.2f}")
                else:  # 끝 포인트
                    segment_num = (i // 2) + 1
                    print(f"[DataBridge] 노드[{i}] = 구간{segment_num} 끝: {optimization_velocity[i]['velocity']:.2f}")
            
            # 경계 노드 동일성 검사
            print("[DataBridge] === 경계 노드 동일성 검사 ===")
            for i in range(0, len(optimization_velocity)-2, 2):
                current_end_idx = i + 1
                next_start_idx = i + 2
                current_end_vel = optimization_velocity[current_end_idx]['velocity']
                next_start_vel = optimization_velocity[next_start_idx]['velocity']
                
                segment_num = (i // 2) + 1
                print(f"[DataBridge] 구간{segment_num}→{segment_num+1}: 노드[{current_end_idx}]({current_end_vel:.2f}) vs 노드[{next_start_idx}]({next_start_vel:.2f})")
                
                # 같은 노드여야 하는데 다른 값인지 확인
                if abs(current_end_vel - next_start_vel) > 0.001:
                    print(f"[DataBridge] ❌ 경계 노드 불일치: 노드[{current_end_idx}] ≠ 노드[{next_start_idx}]")
                else:
                    print(f"[DataBridge] ✅ 경계 노드 일치")
            
            # 연속성 검증 로그
            print("[DataBridge] === 연속성 검증 ===")
            for i in range(0, len(optimization_velocity)-2, 2):
                current_end = optimization_velocity[i+1]['velocity']
                next_start = optimization_velocity[i+2]['velocity']
                diff = abs(current_end - next_start)
                segment_num = (i // 2) + 1
                print(f"[DataBridge] 구간{segment_num} 끝({current_end:.2f}) vs 구간{segment_num+1} 시작({next_start:.2f}) 차이: {diff:.2f}")
                if diff > 0.1:
                    print(f"[DataBridge] ⚠️ 연속성 문제 발견: 구간{segment_num}→{segment_num+1}")
            print("[DataBridge] === 검증 완료 ===")
            
            return optimization_velocity
            
        except Exception as e:
            pass
            return []
    
    def _update_from_anchor_change(self, new_anchor_velocity):
        """앵커 변경 시 전체 그래프 업데이트"""
        try:
            if not self._linear_coefficients or not self._linear_params:
                return []
            
            # 앵커 속도 업데이트
            self._current_anchor_velocity = new_anchor_velocity
            
            # 앵커 기반으로 모든 포인트 재계산
            optimization_velocity = []
            
            for i, (coeff, param) in enumerate(zip(self._linear_coefficients, self._linear_params)):
                if coeff['duration'] <= 0:
                    continue
                
                # 시작 속도: v_i(w) = A_i * w + B_i
                start_velocity = param['A'] * self._current_anchor_velocity + param['B']
                
                # 끝 속도: 거리 제약 적용
                end_velocity = coeff['distance_constraint'] - start_velocity
                
                # 포인트 생성
                start_time = coeff['start_time']
                end_time = start_time + coeff['duration']
                
                optimization_velocity.extend([
                    {'time': start_time, 'velocity': start_velocity},
                    {'time': end_time, 'velocity': end_velocity}
                ])
            
            return optimization_velocity
            
        except Exception as e:
            return []
    
    def _reverse_calculate_anchor(self, point_index, target_velocity):
        """일반 포인트에서 앵커 속도 역계산"""
        try:
            # 해당 포인트가 속한 구간 찾기
            segment_index = point_index // 2  # 각 구간마다 2개 포인트
            
            # 수정된 가드 조건: segment_index 기준으로 검사
            if not self._linear_params or not self._linear_coefficients or segment_index >= len(self._linear_params):
                return target_velocity
            
            param = self._linear_params[segment_index]
            
            # 끝점(odd index) 처리: 시작값으로 환산 후 역계산
            if point_index % 2 == 1:  # 끝점인 경우
                if segment_index < len(self._linear_coefficients):
                    m_i = self._linear_coefficients[segment_index]['distance_constraint']
                    # v_i_equiv = m_i - v_{i+1} (끝점을 시작값으로 환산)
                    v_equiv = m_i - target_velocity
                else:
                    v_equiv = target_velocity
            else:  # 시작점인 경우
                v_equiv = target_velocity
            
            # v_i(w) = A_i * w + B_i에서 w 역계산
            # w = (v_i_equiv - B_i) / A_i
            if abs(param['A']) > 0.001:  # 0으로 나누기 방지
                anchor_velocity = (v_equiv - param['B']) / param['A']
                return anchor_velocity
            
            return target_velocity
            
        except Exception as e:
            return target_velocity
    
    def _parse_float(self, value, default=0.0):
        """문자열을 float로 안전하게 변환"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str) and value.strip():
                return float(value.strip())
            return default
        except (ValueError, TypeError):
            return default
    
    def _update_calculated_values(self):
        """테이블의 계산된 값들 업데이트"""
        try:
            fps = self._project_data['settings']['fps']
            max_acc = self._project_data['settings']['max_acceleration']
            max_dec = self._project_data['settings']['max_deceleration']
            
            for segment in self._project_data['segments']:
                # 7-10열 계산 값 초기화 (테이블에서 전송되지 않으므로 기본값 설정)
                if 'acc_velocity' not in segment:
                    segment['acc_velocity'] = 0.0
                if 'acceleration' not in segment:
                    segment['acceleration'] = 0.0
                if 'duration' not in segment:
                    segment['duration'] = 0.0
                if 'acc_dec_type' not in segment:
                    segment['acc_dec_type'] = ""
                
                # 프레임 정보가 있는 경우 duration 계산
                frame_start = self._parse_float(segment.get('frame_start', 0))
                frame_end = self._parse_float(segment.get('frame_end', 0))
                distance = self._parse_float(segment.get('distance', 0))
                
                if frame_start > 0 and frame_end > 0 and fps > 0:
                    duration = (frame_end - frame_start) / fps
                    segment['duration'] = round(duration, 3)
                    
                    # 평균 속도 계산 (거리와 시간이 있는 경우)
                    if distance > 0 and duration > 0:
                        avg_velocity_ms = distance / duration  # m/s
                        avg_velocity_kmh = avg_velocity_ms * 3.6  # km/h
                        segment['avg_velocity'] = round(avg_velocity_kmh, 2)
                        segment['avg_time'] = round(duration, 3)
                
                # 가속도 검증 (기본값 0 사용)
                acceleration = self._parse_float(segment.get('acceleration', 0))
                uniform_threshold = DEFAULT_UNIFORM_MOTION_THRESHOLD
                
                acc_dec_type = ""
                if abs(acceleration) <= uniform_threshold:
                    # 등속 구간 (임계값 이하)
                    acc_dec_type = "Const (Uniform)"
                elif acceleration > uniform_threshold:
                    # 가속 구간
                    if acceleration <= max_acc:
                        acc_dec_type = "Acc (Valid)"
                    else:
                        acc_dec_type = "Acc (Invalid)"
                else:  # acceleration < -uniform_threshold
                    # 감속 구간
                    if acceleration >= max_dec:
                        acc_dec_type = "Dec (Valid)"
                    else:
                        acc_dec_type = "Dec (Invalid)"
                
                segment['acc_dec_type'] = acc_dec_type
                

            
        except Exception as e:
            pass
    
    def _update_table_from_optimization_data(self):
        """최적화된 그래프 데이터를 기반으로 테이블 업데이트"""
        try:
            optimization_data = self._project_data['graph_data'].get('optimization_velocity', [])
            if not optimization_data:
                return
            
            fps = self._project_data['settings']['fps']
            segments = self._project_data['segments']
            
            # 각 구간별로 최적화 데이터 분석
            for i, segment in enumerate(segments):
                frame_start = self._parse_float(segment.get('frame_start', 0))
                frame_end = self._parse_float(segment.get('frame_end', 0))
                
                if frame_start == 0 or frame_end == 0 or fps == 0:
                    continue
                
                # 구간 시간 범위 계산
                segment_start_time = 0.0
                if i > 0:
                    # 이전 구간들의 시간 합산
                    for j in range(i):
                        prev_start = self._parse_float(segments[j].get('frame_start', 0))
                        prev_end = self._parse_float(segments[j].get('frame_end', 0))
                        if prev_start > 0 and prev_end > 0:
                            segment_start_time += (prev_end - prev_start) / fps
                
                segment_end_time = segment_start_time + (frame_end - frame_start) / fps
                
                # 해당 구간의 최적화 데이터 찾기
                segment_opt_data = []
                for point in optimization_data:
                    if segment_start_time <= point['time'] <= segment_end_time:
                        segment_opt_data.append(point)
                
                if len(segment_opt_data) >= 2:
                    # 가속도 구간 분석
                    first_point = segment_opt_data[0]
                    last_point = segment_opt_data[-1]
                    
                    # 초기 속도와 최종 속도
                    initial_velocity = first_point['velocity']
                    final_velocity = last_point['velocity']
                    
                    # 가속도가 있는 경우
                    vel_diff = abs(final_velocity - initial_velocity)
                    
                    if vel_diff > 0.1:  # 0.1 km/h 임계값
                        # 가속도 계산
                        time_diff = last_point['time'] - first_point['time']
                        if time_diff > 0:
                            vel_diff_ms = (final_velocity - initial_velocity) / 3.6  # km/h to m/s
                            acceleration = vel_diff_ms / time_diff
                            
                            # 테이블 업데이트
                            segment['acceleration'] = round(acceleration, 2)
                            segment['acc_time'] = round(time_diff, 3)
                            segment['acc_velocity'] = round(final_velocity, 2)
                            
                            # 가속도 유효성 검증
                            max_acc = self._project_data['settings']['max_acceleration']
                            max_dec = self._project_data['settings']['max_deceleration']
                            uniform_threshold = DEFAULT_UNIFORM_MOTION_THRESHOLD
                            
                            if abs(acceleration) <= uniform_threshold:
                                # 등속 구간
                                segment['acc_dec_type'] = "Const (Uniform)"
                            elif acceleration > uniform_threshold:
                                # 가속 구간
                                if acceleration <= max_acc:
                                    segment['acc_dec_type'] = "Acc (Valid)"
                                else:
                                    segment['acc_dec_type'] = "Acc (Invalid)"
                            else:  # acceleration < -uniform_threshold
                                # 감속 구간
                                if acceleration >= max_dec:
                                    segment['acc_dec_type'] = "Dec (Valid)"
                                else:
                                    segment['acc_dec_type'] = "Dec (Invalid)"
                    else:
                        # 일정 속도 유지 (등속구간)
                        time_diff = last_point['time'] - first_point['time']
                        segment['acceleration'] = 0.0
                        segment['acc_time'] = round(time_diff, 3)  # 실제 구간 지속시간
                        segment['acc_velocity'] = round(initial_velocity, 2)
                        
                        # 등속구간 유효성 검증
                        uniform_threshold = DEFAULT_UNIFORM_MOTION_THRESHOLD
                        segment['acc_dec_type'] = "Const (Uniform)"
        except Exception as e:
            pass
    
    # === Ground Truth 데이터 처리 ===
    
    def load_ground_truth_csv(self, filepath: str) -> bool:
        """Ground Truth CSV 파일 로드"""
        try:
            import pandas as pd
            
            # CSV 파일 읽기
            df = pd.read_csv(filepath)
            
            # 데이터 검증
            if not self._validate_ground_truth_data(df):
                return False
            
            # 데이터 저장
            ground_truth_data = []
            for _, row in df.iterrows():
                ground_truth_data.append({
                    'time': float(row.iloc[0]),
                    'velocity': float(row.iloc[1])
                })
            
            self._project_data['graph_data']['ground_truth_velocity'] = ground_truth_data
            self._project_data['ground_truth_file'] = filepath
            
            # 그래프 업데이트 알림
            self.graph_data_updated.emit(self._project_data['graph_data'])
            

            return True
            
        except Exception as e:
            pass
            self.error_occurred.emit(f"Ground Truth 파일 로드 중 오류: {e}")
            return False
    
    def _validate_ground_truth_data(self, df) -> bool:
        """Ground Truth 데이터 검증"""
        # 최소 2개 열 확인
        if len(df.columns) < 2:
            self.error_occurred.emit("CSV 파일에는 최소 2개의 열(시간, 속도)이 필요합니다.")
            return False
        
        # 숫자 데이터 확인
        try:
            pd.to_numeric(df.iloc[:, 0])  # 시간
            pd.to_numeric(df.iloc[:, 1])  # 속도
        except:
            self.error_occurred.emit("CSV 파일의 시간과 속도 데이터는 숫자여야 합니다.")
            return False
        
        return True
    
    # === 파일 I/O ===
    
    def save_project(self, filepath: str) -> bool:
        """프로젝트 저장"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._project_data, f, ensure_ascii=False, indent=2)
            
            self._unsaved_changes = False

            return True
            
        except Exception as e:
            pass
            self.error_occurred.emit(f"프로젝트 저장 중 오륙: {e}")
            return False
    
    def load_project(self, filepath: str) -> bool:
        """프로젝트 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._project_data = data
            self._unsaved_changes = False
            
            # 앵커 시스템 초기화 (로드된 데이터로부터 재계산)
            self._linear_coefficients = None
            self._linear_params = None
            self._current_anchor_velocity = None
            
            # 모든 윈도우에 업데이트 알림
            self.table_data_updated.emit({'segments': self._project_data['segments']})
            
            # 로드 직후 최신 알고리즘으로 그래프 재계산
            self._calculate_graph_data()
            

            return True
            
        except Exception as e:
            pass
            self.error_occurred.emit(f"프로젝트 로드 중 오류: {e}")
            return False
    
    # === PC-Crash 연동 ===
    
    def fetch_distance_data(self) -> bool:
        """PC-Crash에서 거리 데이터 가져오기"""
        # TODO: Phase 6에서 구현

        return True
    
    def send_simulation_data(self) -> bool:
        """PC-Crash로 시뮬레이션 데이터 전송"""
        # TODO: Phase 6에서 구현

        return True
    
    # === 유틸리티 메서드 ===
    
    def has_unsaved_changes(self) -> bool:
        """저장되지 않은 변경사항 확인"""
        return self._unsaved_changes
    
    def get_project_data(self) -> Dict[str, Any]:
        """프로젝트 데이터 반환"""
        return self._project_data.copy()
    
    def get_settings(self) -> Dict[str, Any]:
        """설정 데이터 반환"""
        return self._project_data['settings'].copy()
    
    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        self._project_data['settings'].update(settings)
        self._unsaved_changes = True

    
    def cleanup(self):
        """리소스 정리"""
