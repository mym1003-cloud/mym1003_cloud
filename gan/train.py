# 5~8단계: 손실 함수 정의 · GAN 결합 · 학습 루프
import tensorflow as tf
import numpy as np
from config import LATENT_DIM, BATCH_SIZE, LR_G, LR_D, BETA_1

# ── 5단계: 손실 함수 ─────────────────────────────────────────
cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)


def discriminator_loss(real_output, fake_output):
    """판별기 손실: 진짜→1, 가짜→0으로 분류"""
    real_loss = cross_entropy(tf.ones_like(real_output),  real_output)
    fake_loss = cross_entropy(tf.zeros_like(fake_output), fake_output)
    return real_loss + fake_loss


def generator_loss(fake_output):
    """생성기 손실: 판별기가 가짜를 1(진짜)로 분류하도록 유도"""
    return cross_entropy(tf.ones_like(fake_output), fake_output)


# ── 5단계: 옵티마이저 ────────────────────────────────────────
gen_optimizer  = tf.keras.optimizers.Adam(LR_G, beta_1=BETA_1)
disc_optimizer = tf.keras.optimizers.Adam(LR_D, beta_1=BETA_1)


# ── 6단계: 단일 학습 스텝 (GAN 결합) ────────────────────────
@tf.function
def train_step(real_images, generator, discriminator):
    noise = tf.random.normal([BATCH_SIZE, LATENT_DIM])

    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        fake_images = generator(noise, training=True)

        real_output = discriminator(real_images, training=True)
        fake_output = discriminator(fake_images, training=True)

        g_loss = generator_loss(fake_output)
        d_loss = discriminator_loss(real_output, fake_output)

    # 그래디언트 계산 및 적용
    gen_grads  = gen_tape.gradient(g_loss,  generator.trainable_variables)
    disc_grads = disc_tape.gradient(d_loss, discriminator.trainable_variables)

    gen_optimizer.apply_gradients(zip(gen_grads,  generator.trainable_variables))
    disc_optimizer.apply_gradients(zip(disc_grads, discriminator.trainable_variables))

    return g_loss, d_loss


# ── 7~8단계: 전체 학습 루프 ──────────────────────────────────
def train(dataset, generator, discriminator, epochs, sample_fn, sample_every):
    for epoch in range(1, epochs + 1):
        g_losses, d_losses = [], []

        for real_batch in dataset:
            g_loss, d_loss = train_step(real_batch, generator, discriminator)
            g_losses.append(float(g_loss))
            d_losses.append(float(d_loss))

        avg_g = np.mean(g_losses)
        avg_d = np.mean(d_losses)

        if epoch % sample_every == 0 or epoch == 1:
            print(f"[Epoch {epoch:>5}] G Loss: {avg_g:.4f}  D Loss: {avg_d:.4f}")
            sample_fn(epoch)   # 샘플 이미지 저장 (main.py 정의)
