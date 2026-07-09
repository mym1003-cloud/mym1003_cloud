import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

labels = [
    '관리자\n착용인식',
    '근로자\n착용',
    '신뢰\n관리조직',
    '현장\n안전기준',
    '안전냉소\n불신',
    '내행동\n변화이유',
    '내행동\n지속힘',
    '관리자자신\n착용률응답'
]

corr = np.array([
    [ 1.000,  0.871,  0.853, -0.699, -0.699,  0.204,  0.457,  0.709],
    [ 0.871,  1.000,  0.835, -0.521, -0.521,  0.284,  0.534,  0.640],
    [ 0.853,  0.835,  1.000, -0.592, -0.592,  0.430,  0.608,  0.633],
    [-0.699, -0.521, -0.592,  1.000,  1.000,  0.034, -0.236, -0.594],
    [-0.699, -0.521, -0.592,  1.000,  1.000,  0.034, -0.236, -0.594],
    [ 0.204,  0.284,  0.430,  0.034,  0.034,  1.000,  0.590,  0.060],
    [ 0.457,  0.534,  0.608, -0.236, -0.236,  0.590,  1.000,  0.423],
    [ 0.709,  0.640,  0.633, -0.594, -0.594,  0.060,  0.423,  1.000],
])

fig = plt.figure(figsize=(26, 12))
fig.suptitle('안전장구 착용 관련 변수 상관관계 분석',
             fontsize=17, fontweight='bold', y=1.02)

# ── 1. 히트맵 ──────────────────────────────────────────────
ax1 = fig.add_axes([0.02, 0.05, 0.43, 0.88])
lower = np.tril(np.ones_like(corr, dtype=bool))
sns.heatmap(
    corr, mask=~lower,
    annot=True, fmt='.3f',
    cmap='RdYlGn', vmin=-1, vmax=1, center=0,
    xticklabels=labels, yticklabels=labels,
    ax=ax1, linewidths=0.5,
    annot_kws={'size': 9},
    cbar_kws={'shrink': 0.65, 'pad': 0.02}
)
ax1.set_title('상관계수 히트맵', fontsize=13, pad=14)
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=40, ha='right',
                    fontsize=9, linespacing=1.3)
ax1.set_yticklabels(ax1.get_yticklabels(), rotation=0,
                    fontsize=9, linespacing=1.3)
ax1.tick_params(axis='x', pad=5)
ax1.tick_params(axis='y', pad=5)

# ── 2. 네트워크 그래프 ─────────────────────────────────────
ax2 = fig.add_axes([0.49, 0.02, 0.50, 0.94])
ax2.set_xlim(-1.85, 1.85)
ax2.set_ylim(-1.75, 1.75)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('유의미 상관관계 네트워크 (|r| ≥ 0.4)',
              fontsize=13, pad=16, fontweight='bold')

n = len(labels)
node_r = 1.1
# 12시에서 시계방향, 단 상단 노드가 제목과 안 겹치도록 오프셋
angles = np.array([np.pi/2 + 2*np.pi*i/n for i in range(n)])
# 노드 0을 오른쪽(3시)부터 시작해 반시계
angles = np.linspace(np.pi/2, np.pi/2 - 2*np.pi, n, endpoint=False)

pos = {i: (node_r * np.cos(a), node_r * np.sin(a)) for i, a in enumerate(angles)}

# ── 엣지 ───────────────────────────────────────────────────
for i in range(n):
    for j in range(i+1, n):
        r = corr[i, j]
        if abs(r) < 0.4:
            continue
        xi, yi = pos[i]
        xj, yj = pos[j]
        color = '#d73027' if r < 0 else '#1a9850'
        lw = 0.8 + abs(r) * 5
        alpha = min(0.25 + abs(r) * 0.7, 0.95)
        ax2.plot([xi, xj], [yi, yj], color=color,
                 linewidth=lw, alpha=alpha, zorder=1, solid_capstyle='round')

        # |r|>=0.59만 숫자 표시, 노드에 가까운 쪽(1/3 지점)에 배치
        if abs(r) >= 0.59:
            t = 0.33
            mx = xi*t + xj*(1-t)
            my = yi*t + yj*(1-t)
            ax2.text(mx, my, f'{r:.2f}', fontsize=8, ha='center', va='center',
                     zorder=5, fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.18', fc='white',
                               ec='none', alpha=0.85))

# ── 노드 ───────────────────────────────────────────────────
node_colors = ['#2166ac', '#2166ac', '#2166ac',
               '#d73027', '#d73027',
               '#4dac26', '#4dac26', '#2166ac']

for i, (nx, ny) in pos.items():
    ax2.scatter(nx, ny, s=900, c=node_colors[i], zorder=3,
                edgecolors='white', linewidths=2.5)

# ── 노드 레이블: 노드 바로 옆에 붙임 ──────────────────────
label_r = 1.38   # 노드(r=1.1)에서 0.28 떨어진 거리

for i, a in enumerate(angles):
    lx = label_r * np.cos(a)
    ly = label_r * np.sin(a)

    cos_a, sin_a = np.cos(a), np.sin(a)
    ha = 'left' if cos_a > 0.2 else ('right' if cos_a < -0.2 else 'center')
    va = 'bottom' if sin_a > 0.2 else ('top' if sin_a < -0.2 else 'center')

    ax2.text(lx, ly, labels[i],
             fontsize=10, ha=ha, va=va, fontweight='bold',
             linespacing=1.3, zorder=6,
             bbox=dict(boxstyle='round,pad=0.35', fc='white',
                       ec='#999999', alpha=0.95, linewidth=0.8))

# ── 범례 ───────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], color='#1a9850', linewidth=3, label='정적 상관 (r > 0)'),
    Line2D([0], [0], color='#d73027', linewidth=3, label='부적 상관 (r < 0)'),
    Line2D([0], [0], color='gray',    linewidth=1.5, label='선 굵기 ∝ |r|'),
]
ax2.legend(handles=legend_elements, loc='lower right',
           fontsize=9.5, framealpha=0.93, edgecolor='#cccccc',
           bbox_to_anchor=(1.0, 0.0))

out = 'C:/Users/USER/Desktop/안티그래비티/상관관계_그래프.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print('done')
