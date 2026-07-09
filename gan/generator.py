# 3단계: 생성기(Generator) — 무작위 노이즈 → 가짜 이미지
import tensorflow as tf
from tensorflow.keras import layers, Model
from config import LATENT_DIM, IMG_SHAPE


def build_generator() -> Model:
    """
    Dense → Reshape → Conv2DTranspose(업샘플링) 구조의 생성기.
    입력: (batch, LATENT_DIM) 노이즈 벡터
    출력: (batch, 28, 28, 1) tanh 정규화 이미지 [-1, 1]
    """
    inp = layers.Input(shape=(LATENT_DIM,))

    x = layers.Dense(7 * 7 * 256, use_bias=False)(inp)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.2)(x)
    x = layers.Reshape((7, 7, 256))(x)          # 7×7×256

    x = layers.Conv2DTranspose(128, 5, strides=1,
                               padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.2)(x)               # 7×7×128

    x = layers.Conv2DTranspose(64, 5, strides=2,
                               padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.2)(x)               # 14×14×64

    out = layers.Conv2DTranspose(IMG_SHAPE[2], 5, strides=2,
                                 padding='same', use_bias=False,
                                 activation='tanh')(x)  # 28×28×1

    return Model(inp, out, name='Generator')


if __name__ == '__main__':
    g = build_generator()
    g.summary()
