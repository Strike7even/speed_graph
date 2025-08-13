"""
속도 최적화 프로그램 메인 진입점
영상기반 속도분석 한계 극복을 위한 사용자 주도형 속도 최적화 기법
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from velocity_optimizer import VelocityOptimizer

def main():
    """메인 함수"""
    try:
        # High DPI 지원 (QApplication 생성 전에 설정)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # QApplication 생성
        app = QApplication(sys.argv)
        app.setApplicationName("속도 최적화 프로그램")
        app.setApplicationVersion("1.0.0")
        
        # 메인 컨트롤러 생성 및 실행
        optimizer = VelocityOptimizer()
        optimizer.show()
        
        # 이벤트 루프 시작
        exit_code = app.exec_()
        
        return exit_code
        
    except Exception as e:
        pass
        return 1

if __name__ == '__main__':
    sys.exit(main())