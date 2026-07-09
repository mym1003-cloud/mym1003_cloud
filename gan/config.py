# GAN 하이퍼파라미터 및 경로 설정
import os

# 경로
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, 'output')
MODEL_DIR   = os.path.join(BASE_DIR, 'saved_models')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR,  exist_ok=True)

# 모델 구조
LATENT_DIM   = 100     # 생성기 입력 노이즈 차원
IMG_SHAPE    = (28, 28, 1)  # MNIST 이미지 크기

# 학습
EPOCHS       = 10000
BATCH_SIZE   = 128
SAMPLE_EVERY = 1000   # 몇 에포크마다 샘플 이미지 저장

# 옵티마이저
LR_G = 0.0002   # 생성기 학습률
LR_D = 0.0002   # 판별기 학습률
BETA_1 = 0.5    # Adam β₁ (GAN 표준값)
