# 1~2단계 (데이터), 9~10단계 (생성 · 시각화) 통합 실행 스크립트
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config import (LATENT_DIM, EPOCHS, BATCH_SIZE,
                    SAMPLE_EVERY, OUTPUT_DIR, MODEL_DIR)
from generator     import build_generator
from discriminator import build_discriminator
from train         import train


# ── 1단계: 라이브러리 임포트 완료 ────────────────────────────

# ── 2단계: 데이터 로드 및 전처리 ────────────────────────────
def load_dataset():
    (x_train, _), _ = tf.keras.datasets.mnist.load_data()
    x_train = x_train.astype('float32')
    x_train = (x_train - 127.5) / 127.5          # [-1, 1] 정규화
    x_train = x_train[..., np.newaxis]            # (N, 28, 28, 1)
    dataset = (
        tf.data.Dataset
        .from_tensor_slices(x_train)
        .shuffle(60000)
        .batch(BATCH_SIZE, drop_remainder=True)
        .prefetch(tf.data.AUTOTUNE)
    )
    print(f"학습 데이터: {x_train.shape}  배치: {BATCH_SIZE}")
    return dataset


# ── 9단계: 새 샘플 생성 ──────────────────────────────────────
# ── 10단계: 생성 이미지 플로팅 및 저장 ──────────────────────
SEED = tf.random.normal([16, LATENT_DIM])   # 에포크별 동일 노이즈로 진행 추적

def save_samples(epoch, generator):
    preds = generator(SEED, training=False).numpy()   # (16, 28, 28, 1)
    preds = (preds + 1) / 2.0                         # [0, 1] 복원

    fig, axes = plt.subplots(4, 4, figsize=(6, 6))
    fig.suptitle(f'Epoch {epoch}', fontsize=12)
    for ax, img in zip(axes.flatten(), preds):
        ax.imshow(img.squeeze(), cmap='gray', vmin=0, vmax=1)
        ax.axis('off')
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f'epoch_{epoch:05d}.png')
    plt.savefig(path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  → 샘플 저장: {path}")


def main():
    # 모델 구축
    generator     = build_generator()
    discriminator = build_discriminator()
    generator.summary()
    discriminator.summary()

    # 데이터 준비
    dataset = load_dataset()

    # 학습 실행 (7~8단계 루프)
    train(
        dataset      = dataset,
        generator    = generator,
        discriminator= discriminator,
        epochs       = EPOCHS,
        sample_fn    = lambda ep: save_samples(ep, generator),
        sample_every = SAMPLE_EVERY,
    )

    # 모델 저장
    generator.save(os.path.join(MODEL_DIR, 'generator.keras'))
    discriminator.save(os.path.join(MODEL_DIR, 'discriminator.keras'))
    print("학습 완료. 모델 저장됨.")

    # 최종 생성 샘플 16장 출력
    save_samples('final', generator)


if __name__ == '__main__':
    main()
