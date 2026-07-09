
from rdflib import Graph

g = Graph()
g.parse("my_result.ttl", format="turtle")

print("\n--- 🛡️ 현장별 맞춤 안전 지침 분석 ---")

for s, p, o in g:
    subject = str(s).split('#')[-1]
    predicate = str(p).split('#')[-1]
    object_val = str(o).split('#')[-1]
    
    # 여기서부터 들여쓰기가 매우 중요합니다!
    if "Site" in subject and "hasHazard" in predicate:
        print(f"\n[현장 리포트: {subject}]") # if문에 포함되도록 들여쓰기
        
        if "Fall" in object_val:
            print("   ⚠️ 분석 결과: 추락 위험 감지!")
            print("   ✅ 조치 사항: 안전고리 체결 및 안전망 점검 필수")
        elif "Fire" in object_val:
            print("   🔥 분석 결과: 화재 위험 감지!")
            print("   ✅ 조치 사항: 인화물질 제거 및 화기 감시자 배치 확인")
            print("\n--- 🚨 긴급 점검 대상 현장 (추락 위험) ---")
for s, p, o in g:
    if "hasHazard" in str(p) and "Fall" in str(o):
        site_name = str(s).split('#')[-1]
        print(f"⚠️ 즉시 점검 필요: {site_name}")
        # check_result.py 내의 루프 수정 예시
for s, p, o in g:
    # ... (기존 코드)
    if "hasManager" in predicate:
        print(f"👤 담당 관리자: {object_val}")
        