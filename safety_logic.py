import rdflib

# 1. 그래프 생성 및 기본 지식 추가
g = rdflib.Graph()

labor_dept = rdflib.URIRef("http://example.org/LaborDept")
action = rdflib.URIRef("http://example.org/performs")
inspection = rdflib.URIRef("http://example.org/SiteInspection")
g.add((labor_dept, action, inspection))

# 2. 새로운 지식 추가
site_a = rdflib.URIRef("http://example.org/ConstructionSite_A")
has_issue = rdflib.URIRef("http://example.org/hasSafetyIssue")
danger = rdflib.URIRef("http://example.org/FallHazard")
g.add((site_a, has_issue, danger))

# 3. 화면 출력
print("\n--- 업데이트된 지식 목록 ---")
for s, p, o in g:
    print(f"[{s.split('/')[-1]}] --({p.split('/')[-1]})--> [{o.split('/')[-1]}]")
    from rdflib import Namespace
ns1 = Namespace("http://example.org/") # ns1이라는 이름을 정의함

# 4. 결과물 파일로 저장 (가장 중요!)
g.serialize(destination="result.ttl", format="turtle")
print("\n[성공] 'result.ttl' 파일이 생성되었습니다!")
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS

# 1. 그래프 생성 (데이터 보관함)
g = Graph()

# 2. 우리만의 단어장(Namespace) 만들기
# 주소는 가짜여도 상관없지만 형식은 지켜야 합니다.
EX = Namespace("http://example.org/safety#")

# 3. 지식(Triple) 추가하기: [주어, 서술어, 목적어]
# "현장A는 추락위험을 가지고 있다"
g.add((EX.Site_A, EX.hasHazard, EX.Fall))
# "추락은 고위험군에 속한다"
g.add((EX.Fall, EX.riskLevel, EX.High))

# 4. 결과 출력해보기
print("--- 현재 저장된 지식 목록 ---")
for s, p, o in g:
    print(f"주어: {s.split('#')[-1]} | 관계: {p.split('#')[-1]} | 목적어: {o.split('#')[-1]}")

# 5. 파일로 저장하기 (이게 중요!)
# 이 코드를 실행하면 폴더에 'my_result.ttl' 파일이 생깁니다.
g.serialize(destination="my_result.ttl", format="turtle")
print("\n--- 'my_result.ttl' 파일이 생성되었습니다! ---")
# 새로운 현장과 위험 요소 추가
g.add((ns1.ConstructionSite_B, ns1.hasSafetyIssue, ns1.FireHazard))
g.add((ns1.ConstructionSite_C, ns1.hasSafetyIssue, ns1.ElectricHazard))
# 1. 새로운 현장 추가
g.add((ns1.Site_B, ns1.hasHazard, ns1.Fire))

# 2. 새로운 관계 추가 (화재는 중위험군이다)
g.add((ns1.Fire, ns1.riskLevel, ns1.Medium))
# 1. 해결책(Action) 정의
g.add((EX.SafetyNet, RDFS.label, Literal("안전망 설치")))
g.add((EX.Extinguisher, RDFS.label, Literal("소화기 배치")))

# 2. 위험 요소와 해결책 연결
g.add((EX.Fall, EX.requiresAction, EX.SafetyNet))
g.add((EX.Fire, EX.requiresAction, EX.Extinguisher))

g.add((ns1.Site_B, ns1.hasHazard, ns1.Fire))
# 1. 데이터를 추가한 후 (이 부분은 이미 있으실 거예요)
g.add((ns1.Site_B, ns1.hasHazard, ns1.Fire))

# 2. ★매우 중요★ 데이터를 파일로 실제 저장하는 코드
g.serialize(destination="my_result.ttl", format="turtle")
print("--- my_result.ttl 파일이 성공적으로 갱신되었습니다! ---")
# '추락'과 '화재'는 모두 '고위험군'이라고 정의합니다.
g.add((ns1.Fall, ns1.isLevel, ns1.Danger))
g.add((ns1.Fire, ns1.isLevel, ns1.Danger))
# 현장 담당자 정보 추가
g.add((ns1.Site_A, ns1.hasManager, Literal("김철수 대리")))
g.add((ns1.Site_B, ns1.hasManager, Literal("이영희 과장")))
