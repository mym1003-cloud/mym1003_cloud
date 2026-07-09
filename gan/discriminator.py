# 4단계: 판별기(Discriminator) — 이미지 → 진짜(1) / 가짜(0) 분류
import tensorflow as tf
from tensorflow.keras import layers, Model
from config import IMG_SHAPE


def build_discriminator() -> Model:
    """
    Conv2D(다운샘플링) → Dense 구조의 판별기.
    입력: (batch, 28, 28, 1) 이미지
    출력: (batch, 1) 로짓(sigmoid 이전 값)
    """
    inp = layers.Input(shape=IMG_SHAPE)

    x = layers.Conv2D(64, 5, strides=2, padding='same')(inp)
    x = layers.LeakyReLU(0.2)(x)
    x = layers.Dropout(0.3)(x)                 # 14×14×64

    x = layers.Conv2D(128, 5, strides=2, padding='same')(x)
    x = layers.LeakyReLU(0.2)(x)
    x = layers.Dropout(0.3)(x)                 # 7×7×128

    x = layers.Flatten()(x)
    out = layers.Dense(1)(x)                   # 로짓 (BinaryCrossentropy(from_logits=True))

    return Model(inp, out, name='Discriminator')


if __name__ == '__main__':
    d = build_discriminator()
    d.summary()
