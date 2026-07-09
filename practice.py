import rdflib

# 1. 빈 그래프(지식 저장소) 생성
g = rdflib.Graph()

# 2. 지식 추가 (노동부 직원 시나리오 예시)
# 주어: 노동부직원, 서술어: 수행한다, 목적어: 현장감찰
labor_dept = rdflib.URIRef("http://example.org/LaborDept")
action = rdflib.URIRef("http://example.org/performs")
inspection = rdflib.URIRef("http://example.org/SiteInspection")

g.add((labor_dept, action, inspection))

# 3. 결과 출력
print("--- 온톨로지 데이터 생성 완료 ---")
for s, p, o in g:
    print(f"지식: {s} -> {p} -> {o}")
