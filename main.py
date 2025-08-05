"""
속도 최적화 프로그램 메인 진입점
영상기반 속도분석 한계 극복을 위한 사용자 주도형 속도 최적화 기법
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from velocity_optimizer import VelocityOptimizer

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('speed_graph.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # High DPI 지원 (QApplication 생성 전에 설정)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # QApplication 생성
        app = QApplication(sys.argv)
        app.setApplicationName("속도 최적화 프로그램")
        app.setApplicationVersion("1.0.0")
        
        logger.info("애플리케이션 시작")
        
        # 메인 컨트롤러 생성 및 실행
        optimizer = VelocityOptimizer()
        optimizer.show()
        
        # 이벤트 루프 시작
        exit_code = app.exec_()
        
        logger.info(f"애플리케이션 종료 (코드: {exit_code})")
        return exit_code
        
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())