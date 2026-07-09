"""
논문 목차/표목차/그림목차 페이지 번호 자동 업데이트

구조:
- 전반부(앞부분): Word 페이지 1~16 → 논문 로마자 페이지 ⅰ~ⅹⅵ
- 본문: Word 페이지 17~ → 논문 아라비아 페이지 1~(Word페이지-16)
"""

import win32com.client
import re
import difflib
import shutil

DOC_PATH  = r'C:\Users\USER\Desktop\안티그래비티\thesis\thesis.docx.docx'
BACKUP    = r'C:\Users\USER\Desktop\안티그래비티\thesis\thesis_backup.docx'
OUTPUT    = r'C:\Users\USER\Desktop\안티그래비티\thesis\thesis_updated.docx'

wdActiveEndPageNumber = 3

# 로마숫자 변환 (1~20)
ROMAN = {
    1:'ⅰ',2:'ⅱ',3:'ⅲ',4:'ⅳ',5:'ⅴ',
    6:'ⅵ',7:'ⅶ',8:'ⅷ',9:'ⅸ',10:'ⅹ',
    11:'ⅺ',12:'ⅻ',13:'ⅹⅲ',14:'ⅹⅳ',15:'ⅹⅴ',
    16:'ⅹⅵ',17:'ⅹⅶ',18:'ⅹⅷ',19:'ⅹⅸ',20:'ⅹⅹ',
}
ROMAN_UPPER = {v.upper():v for v in ROMAN.values()}


def normalize(text):
    return re.sub(r'\s+', '', text).strip()


def similarity(a, b):
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def best_match(query, candidates, threshold=0.55):
    """candidates = list of (text, page_num). 가장 유사한 항목의 page_num 반환."""
    best_s, best_p = 0, None
    q = normalize(query)
    for text, page in candidates:
        if not text:
            continue
        s = difflib.SequenceMatcher(None, q, normalize(text)).ratio()
        if s > best_s:
            best_s, best_p = s, page
    return best_p if best_s >= threshold else None, best_s


def caption_match(caption, candidates):
    """'<표 N-M>' 또는 '<그림 N-M>' 정확 매칭"""
    key = normalize(re.sub(r'[<>]', '', caption))
    for text, page in candidates:
        t = normalize(re.sub(r'[<>]', '', text))
        if t.startswith(key) or key == t[:len(key)]:
            return page
    return None


def to_thesis_page(word_page, body_start_word_page):
    """Word 시퀀셜 페이지 → 논문 표시 페이지 문자열"""
    offset = body_start_word_page - 1
    if word_page >= body_start_word_page:
        return str(word_page - offset)
    else:
        roman_num = word_page  # 전반부: Word 페이지 = 로마자 번호 (1=ⅰ)
        return ROMAN.get(roman_num, str(roman_num))


def main():
    # 1. 백업
    print('[1] 파일 백업...')
    shutil.copy2(DOC_PATH, BACKUP)

    # 2. Word 열기 및 Track Changes 수락
    print('[2] Word 열기 및 변경추적 수락...')
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False

    try:
        doc = word.Documents.Open(DOC_PATH)
        doc.AcceptAllRevisions()

        # 3. 전체 단락 + 페이지 번호 수집
        print('[3] 단락별 페이지 번호 수집 중...')
        total = doc.Paragraphs.Count
        all_paras = []  # [(text, word_page)]

        for i, para in enumerate(doc.Paragraphs):
            if i % 200 == 0:
                print(f'    {i}/{total}')
            try:
                text = para.Range.Text.rstrip('\r\n\x07').strip()
                page = para.Range.Information(wdActiveEndPageNumber)
                all_paras.append((text, page, i))
            except Exception:
                all_paras.append(('', None, i))

        print(f'    수집 완료 ({len(all_paras)}개)')

        # 4. 본문 시작 위치(제 1 장) 찾기
        body_start_page = None
        body_start_idx = None
        toc_found = False

        for text, page, idx in all_paras:
            if not text:
                continue
            if '제 1 장' in text and '서' in text and len(text) < 20:
                if '\t' in text:  # 탭 있으면 목차 항목
                    toc_found = True
                elif toc_found:  # 목차 항목 이후 첫 번째 실제 헤딩
                    body_start_page = page
                    body_start_idx = idx
                    print(f'    본문 시작: Word 페이지 {page} (단락 인덱스 {idx})')
                    break

        if not body_start_page:
            print('    !! 본문 시작 위치를 찾지 못했습니다. 기본값 17 사용')
            body_start_page = 17

        offset = body_start_page - 1
        print(f'    페이지 오프셋: {offset} (본문 1페이지 = Word {body_start_page}페이지)')

        # 5. 목차/표목차/그림목차 영역 분리
        # TOC 영역: 본문 시작 이전 (탭 포함 단락)
        # 본문 영역: 본문 시작 이후
        toc_paras = []   # (text, word_page, idx) - 목차 항목들
        body_paras = []  # (text, word_page) - 본문 내용

        for text, page, idx in all_paras:
            if not text:
                continue
            if idx < body_start_idx:
                if '\t' in text:  # 탭 있으면 목차 항목
                    toc_paras.append((text, page, idx))
            else:
                body_paras.append((text, page))

        print(f'    목차 항목 수: {len(toc_paras)}, 본문 단락 수: {len(body_paras)}')

        # 전반부 항목도 페이지 매칭 위해 별도 분리
        frontmatter_paras = [(t, p) for t, p, _ in all_paras if t and '\t' not in t and idx < body_start_idx]

        # 6. 목차 항목별 올바른 페이지 번호 계산
        print('[4] 페이지 번호 매칭 중...')
        updates = {}  # {word_com_idx: new_page_str}

        for toc_text, _, toc_idx in toc_paras:
            parts = toc_text.split('\t')
            if len(parts) < 2:
                continue
            title = parts[0].strip()
            current_page = parts[-1].strip()

            # 현재 로마자 페이지인지 아닌지 판단
            is_roman = any(c in current_page for c in 'ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹⅺⅻ')

            # 전반부 특수 항목
            if title in ('표 목 차', '그림목차', '그림 목 차', '감사의 글', '논문개요',
                         '참고문헌', 'Abstract', '부    록', '부록', '목    차', '목차'):
                # 전체 단락에서 (탭 없이) 해당 텍스트 찾기
                for bt, bp in (frontmatter_paras + body_paras):
                    if title.replace(' ', '') in bt.replace(' ', '') and '\t' not in bt and len(bt) < 25:
                        new_page = to_thesis_page(bp, body_start_page)
                        if new_page != current_page:
                            updates[toc_idx] = new_page
                            print(f'    [{toc_idx:4d}] "{title}" → {new_page!r} (이전: {current_page!r})')
                        break
                continue

            # 장/절/항 본문 매칭
            new_word_page, score = best_match(title, body_paras, threshold=0.60)
            if new_word_page:
                new_page = to_thesis_page(new_word_page, body_start_page)
                if new_page != current_page.strip():
                    updates[toc_idx] = new_page
                    print(f'    [{toc_idx:4d}] "{title[:45]}" → {new_page!r} (이전: {current_page!r}, 유사도 {score:.2f})')
                continue

            # 표/그림 캡션 매칭
            if title.startswith('<표') or title.startswith('<그림'):
                cp = caption_match(title, body_paras)
                if cp:
                    new_page = to_thesis_page(cp, body_start_page)
                    if new_page != current_page.strip():
                        updates[toc_idx] = new_page
                        print(f'    [{toc_idx:4d}] "{title[:45]}" → {new_page!r} (이전: {current_page!r})')

        print(f'\n    총 {len(updates)}개 업데이트 예정')

        # 7. 문서에서 직접 페이지 번호 수정
        print('[5] 문서 수정 중...')
        para_list = list(doc.Paragraphs)

        for idx, new_page in updates.items():
            if idx >= len(para_list):
                continue
            try:
                para = para_list[idx]
                full_text = para.Range.Text.rstrip('\r\n\x07')
                if '\t' not in full_text:
                    continue

                tab_pos = full_text.rfind('\t')
                old_page = full_text[tab_pos + 1:].rstrip('\r\n\x07')
                # 앞 공백 보존
                leading = re.match(r'^(\s*)', old_page).group(1)

                rng = para.Range
                rng.Start = rng.Start + tab_pos + 1
                rng.End = para.Range.End - 1
                rng.Text = leading + new_page

            except Exception as e:
                print(f'    단락 {idx} 수정 오류: {e}')

        # 8. 저장
        print(f'[6] 저장: {OUTPUT}')
        doc.SaveAs2(OUTPUT)
        doc.Close()
        print('    완료!')

    finally:
        word.Quit()

    print('\n=== 작업 완료 ===')
    print(f'백업: {BACKUP}')
    print(f'결과: {OUTPUT}')


if __name__ == '__main__':
    main()
