from ultralytics import YOLO

# 1. 모델 로드 (설치된 v11 세그먼테이션 모델)
model = YOLO('yolo11n-seg.pt')

# 2. 이미지 분석 수행 
# (인터넷 이미지 주소나 컴퓨터에 있는 사진 파일명을 넣으면 됩니다)
results = model('https://ultralytics.com/images/bus.jpg') 

print("\n" + "="*50)
print("🔍 AI 분석 결과 데이터 추출")
print("="*50)

for result in results:
    # A. 바운딩 박스 (네모 칸 좌표)
    boxes = result.boxes
    for box in boxes:
        # 클래스 번호를 이름으로 변환 (예: 0번 -> person)
        cls = int(box.cls[0])
        name = model.names[cls]
        conf = float(box.conf[0])
        print(f"📦 객체: {name:10} | 정확도: {conf:.2f} | 좌표: {box.xyxy[0].tolist()}")

    # B. 세그먼테이션 (다각형 좌표)
    if result.masks:
        print("\n🌈 세그먼테이션 마스크 검출 완료")
        # 첫 번째 객체의 테두리 점 5개만 샘플로 출력
        print(f"📍 첫 번째 객체 테두리 좌표 샘플: {result.masks.xy[0][:5]}")

    # C. 결과 이미지 저장
    result.save(filename='final_analysis.jpg')
    print("\n✅ 시각화 파일 저장 완료: final_analysis.jpg")
    