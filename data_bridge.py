"""
DataBridge - 데이터 통신 허브
모든 모듈 간 데이터 실시간 동기화 및 통신 중재
"""

import json
import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

from utils.constants import (
    DEFAULT_MAX_ACCELERATION, DEFAULT_MAX_DECELERATION,
    DEFAULT_SEGMENTS, DEFAULT_FPS
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
        self.logger = logging.getLogger(__name__)
        
        # 연결된 윈도우 참조
        self.table_window = None
        self.graph_window = None
        
        # 데이터 저장소
        self._project_data = self._initialize_project_data()
        self._unsaved_changes = False
        
        self.logger.info("DataBridge 초기화 완료")
    
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
        self.logger.info("윈도우 참조 설정 완료")
    
    # === 데이터 동기화 메서드 ===
    
    def update_from_table(self, table_data: Dict[str, Any]):
        """테이블에서 데이터 업데이트"""
        try:
            self.logger.debug("테이블 데이터 업데이트 시작")
            
            # 세그먼트 데이터 업데이트
            if 'segments' in table_data:
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
            
            self.logger.debug("테이블 데이터 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"테이블 데이터 업데이트 실패: {e}")
            self.error_occurred.emit(f"테이블 데이터 업데이트 중 오류: {e}")
    
    def update_from_graph(self, graph_data: Dict[str, Any]):
        """그래프에서 데이터 업데이트"""
        try:
            self.logger.debug("그래프 데이터 업데이트 시작")
            
            # 최적화 속도 데이터 업데이트
            if 'optimization_velocity' in graph_data:
                self._project_data['graph_data']['optimization_velocity'] = graph_data['optimization_velocity']
            
            # 테이블 데이터 역산 및 업데이트
            self._update_table_from_optimization_data()
            
            # 변경사항 플래그 설정
            self._unsaved_changes = True
            
            # 테이블 윈도우에 업데이트 알림
            self.table_data_updated.emit(self._project_data['segments'])
            
            self.logger.debug("그래프 데이터 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"그래프 데이터 업데이트 실패: {e}")
            self.error_occurred.emit(f"그래프 데이터 업데이트 중 오류: {e}")
    
    def _calculate_graph_data(self):
        """테이블 데이터를 기반으로 그래프 데이터 계산"""
        try:
            self.logger.debug("그래프 데이터 계산 시작")
            
            # 기존 최적화 속도 데이터 초기화
            optimization_velocity = []
            video_analysis_velocity = []
            
            current_time = 0.0
            fps = self._project_data['settings']['fps']
            
            for segment in self._project_data['segments']:
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
                    video_analysis_velocity.append({
                        'time': current_time,
                        'velocity': avg_velocity
                    })
                    video_analysis_velocity.append({
                        'time': current_time + segment_duration,
                        'velocity': avg_velocity
                    })
                    
                    # Optimization 데이터 (가속도 적용)
                    if acc_time > 0 and acc_velocity > 0:
                        # 가속/감속 적용된 최적화 속도
                        optimization_velocity.append({
                            'time': current_time,
                            'velocity': avg_velocity
                        })
                        
                        # 가속/감속 구간
                        optimization_velocity.append({
                            'time': current_time + acc_time,
                            'velocity': acc_velocity
                        })
                        
                        # 남은 구간 (일정 속도)
                        remaining_time = segment_duration - acc_time
                        if remaining_time > 0:
                            optimization_velocity.append({
                                'time': current_time + segment_duration,
                                'velocity': acc_velocity
                            })
                    else:
                        # 일정 속도 유지
                        optimization_velocity.append({
                            'time': current_time,
                            'velocity': avg_velocity
                        })
                        optimization_velocity.append({
                            'time': current_time + segment_duration,
                            'velocity': avg_velocity
                        })
                    
                    current_time += segment_duration
            
            # 그래프 데이터 업데이트
            self._project_data['graph_data']['optimization_velocity'] = optimization_velocity
            self._project_data['graph_data']['video_analysis_velocity'] = video_analysis_velocity
            
            # 테이블에서 계산된 값들 업데이트
            self._update_calculated_values()
            
            self.logger.debug(f"그래프 데이터 계산 완료: {len(optimization_velocity)}개 포인트")
            
        except Exception as e:
            self.logger.error(f"그래프 데이터 계산 실패: {e}")
            self.error_occurred.emit(f"그래프 데이터 계산 중 오류: {e}")
    
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
                
                # 가속도 검증
                acceleration = self._parse_float(segment.get('acceleration', 0))
                if acceleration != 0:
                    acc_dec_type = ""
                    if acceleration > 0:
                        if acceleration <= max_acc:
                            acc_dec_type = "Acc (Valid)"
                        else:
                            acc_dec_type = "Acc (Invalid)"
                    else:
                        if acceleration >= max_dec:
                            acc_dec_type = "Dec (Valid)"
                        else:
                            acc_dec_type = "Dec (Invalid)"
                    
                    segment['acc_dec_type'] = acc_dec_type
                
            self.logger.debug("계산된 값 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"계산된 값 업데이트 실패: {e}")
    
    def _update_table_from_optimization_data(self):
        """최적화된 그래프 데이터를 기반으로 테이블 업데이트"""
        # TODO: Phase 4에서 구현
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
            
            self.logger.info(f"Ground Truth 파일 로드 완료: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ground Truth 파일 로드 실패: {e}")
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
            self.logger.info(f"프로젝트 저장 완료: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"프로젝트 저장 실패: {e}")
            self.error_occurred.emit(f"프로젝트 저장 중 오류: {e}")
            return False
    
    def load_project(self, filepath: str) -> bool:
        """프로젝트 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._project_data = data
            self._unsaved_changes = False
            
            # 모든 윈도우에 업데이트 알림
            self.table_data_updated.emit(self._project_data['segments'])
            self.graph_data_updated.emit(self._project_data['graph_data'])
            
            self.logger.info(f"프로젝트 로드 완료: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"프로젝트 로드 실패: {e}")
            self.error_occurred.emit(f"프로젝트 로드 중 오류: {e}")
            return False
    
    # === PC-Crash 연동 ===
    
    def fetch_distance_data(self) -> bool:
        """PC-Crash에서 거리 데이터 가져오기"""
        # TODO: Phase 6에서 구현
        self.logger.info("PC-Crash 거리 데이터 가져오기 요청")
        return True
    
    def send_simulation_data(self) -> bool:
        """PC-Crash로 시뮬레이션 데이터 전송"""
        # TODO: Phase 6에서 구현
        self.logger.info("PC-Crash 시뮬레이션 데이터 전송 요청")
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
        self.logger.info("설정 업데이트 완료")
    
    def cleanup(self):
        """리소스 정리"""
        self.logger.info("DataBridge 리소스 정리")