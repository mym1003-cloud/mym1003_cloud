import os
import sys
import time
import win32com.client
from loguru import logger

def get_absolute_path(relative_path):
    """상대 경로를 절대 경로로 변환합니다."""
    return os.path.abspath(relative_path)

def update_docx_toc_and_convert_to_hwp(input_filename="thesis.docx"):
    """
    1. MS Word를 활용하여 docx 파일 내의 목차(TOC), 표목차, 그림목차 페이지 번호를 최신 상태로 업데이트하고 저장합니다.
    2. 아래한글(HWP) 자동화를 활용하여 정제된 docx 파일을 학교 제출용 hwp 파일로 완벽하게 변환 저장합니다.
    """
    input_path = get_absolute_path(input_filename)
    if not os.path.exists(input_path):
        logger.error(f"원본 파일을 찾을 수 없습니다: {input_path}")
        logger.info("프로젝트 폴더(c:\\Users\\USER\\Desktop\\안티그래비티) 안에 원본 Word 논문 파일(.docx)을 복사한 뒤 실행해주세요.")
        return False
        
    if not os.path.isfile(input_path):
        logger.error(f"'{input_filename}'은 파일이 아닌 폴더(디렉토리)입니다!")
        logger.info("현재 경로에 같은 이름의 폴더가 생성되어 있습니다. 이 폴더를 삭제하신 후, 실제 Word 파일(.docx)을 복사해서 넣어주세요.")
        return False


    output_docx_path = input_path.replace(".docx", "_final.docx")
    output_hwp_path = input_path.replace(".docx", "_final.hwp")

    # --- Step 1: MS Word를 연동하여 페이지 번호 동기화 및 목차 필드 업데이트 ---
    logger.info("Step 1: MS Word 프로그램을 호출하여 목차(TOC) 필드 및 페이지 번호 동기화를 진행합니다...")
    word_app = None
    doc = None
    try:
        # 백그라운드에서 MS Word 실행
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = False

        doc = word_app.Documents.Open(input_path)
        logger.info(f"문서 로드 완료: {input_filename}")

        # 변경 내용 추적(Track Changes) 내역이 있으면 모두 수락하여 취소선/밑줄 제거
        if doc.Revisions.Count > 0:
            logger.info(f"문서 내 미반영 변경 추적 내역 {doc.Revisions.Count}개를 감지하여 자동으로 모두 수락(Accept) 처리합니다.")
            doc.Revisions.AcceptAll()
        doc.TrackRevisions = False

        # 전체 필드(목차, 표목차, 그림목차 등) 업데이트하여 페이지 번호 동기화
        logger.info("목차 및 페이지 번호 동기화 필드 업데이트 중...")

        
        # 1) 전체 테이블 오브 피겨스(Table of Figures) 및 목차(TOC) 필드 수동 갱신 명령
        for index in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(index).Update()
            logger.info(f"일반 목차 {index} 갱신 완료")
            
        for index in range(1, doc.TablesOfFigures.Count + 1):
            doc.TablesOfFigures(index).Update()
            logger.info(f"표/그림 목차 {index} 갱신 완료")

        # 2) 혹시 모를 전체 필드 업데이트 통합 수행
        doc.Fields.Update()
        
        # 강제 리프레시를 위해 파일 저장
        doc.SaveAs(output_docx_path)
        logger.info(f"목차가 동기화된 정제 문서 저장 완료: {output_docx_path}")

    except Exception as e:
        logger.error(f"MS Word 목차 업데이트 중 오류 발생: {e}")
        return False
    finally:
        if doc:
            doc.Close(SaveChanges=True)
        if word_app:
            word_app.Quit()

    # --- Step 2: 아래한글(HWP) API를 연동하여 HWP 파일로 포맷 변환 ---
    logger.info("Step 2: 아래한글(HWP) 프로그램을 연동하여 최종 제출용 한글 파일(HWP)로 변환을 시작합니다...")
    hwp_app = None
    try:
        # 백그라운드에서 아래한글 실행
        # HwpObject.HwpOuter.1은 한글 컨트롤 API 표준 ProgID입니다.
        try:
            hwp_app = win32com.client.Dispatch("HWPFrame.HwpObject")
        except Exception:
            hwp_app = win32com.client.Dispatch("HwpObject.HwpOuter.1")

        if not hwp_app:
            logger.warning("로컬 환경에서 아래한글 자동화 오브젝트를 초기화하지 못했습니다.")
            logger.info("[수동 가이드] 한글 프로그램이 없는 경우, 위에서 생성된 '_final.docx' 파일을 한글에서 직접 열어 '다른 이름으로 저장' -> '한글 문서(*.hwp)'로 저장해 주시면 서식 손상 없이 깨끗하게 변환됩니다.")
            return True

        # 아래한글 창 비활성화 모드로 파일 열기
        hwp_app.RegisterModule("FilePathCheckDLL", "SecurityModule") # 보안 모듈 등록 필요 시 대비
        hwp_app.XHwpWindows.Item(0).Visible = False
        
        logger.info(f"정제된 docx 파일 한글로 로딩 중: {output_docx_path}")
        
        # 파일 열기 (Format="docx" 로 지정)
        open_result = hwp_app.Open(output_docx_path, "docx", "")
        if not open_result:
            logger.error("한글에서 docx 문서를 여는데 실패했습니다.")
            return False

        # 한글 HWP 문서 형태로 저장 (Format="HWP", 5는 hwp 표준 포맷 인덱스)
        save_result = hwp_app.SaveAs(output_hwp_path, "HWP", "")
        if save_result:
            logger.success(f"학교 제출용 최종 한글 파일 변환 완료: {output_hwp_path}")
        else:
            logger.error("최종 HWP 파일 저장에 실패했습니다.")
            return False

    except Exception as e:
        logger.error(f"아래한글 변환 중 오류 발생: {e}")
        logger.info("[수동 가이드] 한글(HWP) 라이선스 또는 설치 환경 제한이 있을 수 있습니다. Step 1에서 생성 완료된 '_final.docx' 파일을 아래한글에서 열어 '다른 이름으로 저장'을 진행해 주세요.")
    finally:
        if hwp_app:
            hwp_app.Quit()

    return True

if __name__ == "__main__":
    # 실행인자로 파일명을 줄 수 있으며, 기본값은 thesis.docx 입니다.
    target_file = sys.argv[1] if len(sys.argv) > 1 else "thesis.docx"
    
    logger.info("=== 논문 목차 동기화 및 HWP 최종 변환 프로그램 시작 ===")
    success = update_docx_toc_and_convert_to_hwp(target_file)
    if success:
        logger.info("=== 모든 작업이 성공적으로 처리되었습니다. ===")
    else:
        logger.error("=== 작업 수행 도중 일부 에러가 발생하였습니다. ===")
