import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import statsmodels.api as sm

import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

# CSV 파일 읽기
df = pd.read_csv('csv_1분석전용_귀인요인.csv', encoding='utf-8-sig')
df.columns = df.columns.str.strip().str.replace('\n','')
# 숫자형 변환
num_cols = [c for c in df.columns if c not in ['응답구분','성별','연령','경력','프로젝트기간','현장규모']]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')

print(f"[OK] 데이터 로드: 응답자 {df.shape[0]}명, 변수 {df.shape[1]}개")

# ── 요인분석 ──────────────────────────────────────────────────
from sklearn.decomposition import FactorAnalysis

def kmo_bartlett(data):
    X = data.values
    n, p = X.shape
    corr = np.corrcoef(X.T)
    corr_inv = np.linalg.pinv(corr)
    num = np.sum(corr**2) - np.sum(np.diag(corr)**2)
    denom = num + np.sum(corr_inv**2) - np.sum(np.diag(corr_inv)**2)
    kmo = num / denom if denom != 0 else 0
    det = max(np.linalg.det(corr), 1e-10)
    chi2 = -(n-1-(2*p+5)/6) * np.log(det)
    df_b = p*(p-1)/2
    from scipy.stats import chi2 as chi2dist
    p_val = 1 - chi2dist.cdf(chi2, df_b)
    return kmo, chi2, p_val

def varimax(loadings, max_iter=1000, tol=1e-6):
    n, k = loadings.shape
    rotation = np.eye(k)
    for _ in range(max_iter):
        old = rotation.copy()
        for i in range(k):
            for j in range(i+1, k):
                L = loadings @ rotation
                u = L[:,i]**2 - L[:,j]**2
                v = 2*L[:,i]*L[:,j]
                A = np.sum(u); B = np.sum(v)
                C = np.sum(u**2 - v**2); D = 2*np.sum(u*v)
                num2 = D - 2*A*B/n
                den = C - (A**2-B**2)/n
                angle = np.arctan2(num2, den) / 4
                c, s = np.cos(angle), np.sin(angle)
                R = np.eye(k)
                R[i,i]=c; R[j,j]=c; R[i,j]=-s; R[j,i]=s
                rotation = rotation @ R
        if np.max(np.abs(rotation-old)) < tol:
            break
    return loadings @ rotation

def run_fa(data, cols, n_factors, title):
    exist = [c for c in cols if c in data.columns]
    d = data[exist].dropna()
    kmo, chi2, p_val = kmo_bartlett(d)
    print(f"\n{'='*65}")
    print(f"  {title}  (n={len(d)})")
    print(f"{'='*65}")
    print(f"  KMO={kmo:.3f}  Bartlett chi2={chi2:.1f}  p={p_val:.4f}")
    fa = FactorAnalysis(n_components=n_factors, random_state=0)
    fa.fit(d)
    ld_rot = varimax(fa.components_.T)
    fnames = [f'F{i+1}' for i in range(n_factors)]
    ld = pd.DataFrame(ld_rot, index=exist, columns=fnames).round(3)
    print(f"\n  요인부하량 (|.4| 이상 유의):")
    hdr = f"  {'변수':<10}" + "".join(f"{f:>9}" for f in fnames)
    print(hdr)
    for idx, row in ld.iterrows():
        line = f"  {idx:<10}"
        for v in row:
            mark = "**" if abs(v)>=0.4 else "  "
            line += f" {v:>6.3f}{mark}"
        print(line)
    return ld

A_COLS  = ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12','FCYN1','FCYN2','FCYN3','FCYN4']
run_fa(df, A_COLS, 3, "A그룹+FCYN 요인분석 (3요인, Varimax)")

B_COLS  = ['B13','B14','B15','B16','B17','B18','DT1','DT2','DT3','DT5','DT6','EN1','EN2','EN3','EN4','EN5','EN6']
run_fa(df, B_COLS, 3, "B+DT+EN 요인분석 (3요인, Varimax)")

# ── 잠재변수 생성 ────────────────────────────────────────────
print("\n\n" + "="*65)
print("  잠재변수 생성 (SPSS 결과 기반)")
print("="*65)
LATENT = {
    '내적귀인':     ['A1','A2','A3','A5','A6','A7','A10'],
    '통제위인':     ['FCYN1','FCYN2','FCYN3','FCYN4'],
    '외적귀인':     ['A9','A11','A12'],
    '행동요인_B':   ['B13','B14','B15','B16','B17'],
    '동기요인_DT':  ['DT1','DT2','DT3','DT5','DT6'],
    '환경요인_EN1': ['EN1','EN2','EN3','EN4'],
    '환경요인_EN2': ['EN5','EN6'],
}
for name, cols in LATENT.items():
    exist = [c for c in cols if c in df.columns]
    df[name] = df[exist].mean(axis=1)
    print(f"  {name:<15}: {len(exist)}문항  M={df[name].mean():.3f}  SD={df[name].std():.3f}")

LV = list(LATENT.keys())

# ── 신뢰도 분석 ──────────────────────────────────────────────
print("\n\n" + "="*65)
print("  신뢰도 분석  Cronbach alpha")
print("="*65)
print(f"  {'변수':<15} {'문항':>4} {'alpha':>7}  {'판정'}")
print(f"  {'-'*50}")
for name, cols in LATENT.items():
    exist = [c for c in cols if c in df.columns]
    d = df[exist].dropna()
    if len(exist) >= 2 and len(d) > 2:
        k = len(exist)
        item_var = d.var(axis=0, ddof=1).sum()
        total_var = d.sum(axis=1).var(ddof=1)
        a = (k/(k-1)) * (1 - item_var/total_var)
        g = '우수(>=.9)' if a>=.9 else '양호(>=.8)' if a>=.8 else '수용(>=.7)' if a>=.7 else '미흡(<.7)'
        print(f"  {name:<15} {k:>4}   {a:>6.3f}  {g}")

# ── 기술통계 ─────────────────────────────────────────────────
print("\n\n" + "="*65)
print("  기술통계 + 정규성 검정 (Shapiro-Wilk)")
print("="*65)
print(f"  {'변수':<15} {'n':>4} {'평균':>6} {'SD':>6} {'왜도':>6} {'첨도':>6} {'SW_p':>8} {'정규성':>6}")
print(f"  {'-'*62}")
for v in LV:
    d = df[v].dropna()
    sw_stat, sw_p = stats.shapiro(d)
    norm = 'OK' if sw_p>.05 else '비정규'
    print(f"  {v:<15} {len(d):>4} {d.mean():>6.3f} {d.std():>6.3f} {d.skew():>6.3f} {d.kurtosis():>6.3f} {sw_p:>8.4f} {norm:>6}")

# ── 상관관계 분석 ────────────────────────────────────────────
print("\n\n" + "="*65)
print("  상관관계 분석 (Pearson r)")
print("="*65)
for i, v1 in enumerate(LV):
    for v2 in LV[i+1:]:
        d12 = df[[v1,v2]].dropna()
        r, p = stats.pearsonr(d12[v1], d12[v2])
        sig = '***' if p<.001 else '**' if p<.01 else '*' if p<.05 else 'n.s.'
        print(f"  {v1:<15} <-> {v2:<15}: r={r:+.3f}  p={p:.4f}  {sig}")

# ── 회귀분석 ─────────────────────────────────────────────────
print("\n\n" + "="*65)
print("  회귀분석  행동요인_B ~ 내적귀인 + 통제위인 + 외적귀인")
print("="*65)
X_VARS = ['내적귀인','통제위인','외적귀인']
Y_VAR  = '행동요인_B'
reg = df[X_VARS+[Y_VAR]].dropna()
X = sm.add_constant(reg[X_VARS]); Y = reg[Y_VAR]
m = sm.OLS(Y, X).fit()
print(f"  n={int(m.nobs)}  R²={m.rsquared:.3f}  수정R²={m.rsquared_adj:.3f}  F={m.fvalue:.3f}  p={m.f_pvalue:.4f}")
print(f"\n  {'변수':<15} {'β':>8} {'SE':>7} {'t':>7} {'p':>9} {'유의':>5}")
print(f"  {'-'*52}")
for var in m.params.index:
    sig = '***' if m.pvalues[var]<.001 else '**' if m.pvalues[var]<.01 else '*' if m.pvalues[var]<.05 else 'n.s.'
    print(f"  {var:<15} {m.params[var]:>8.3f} {m.bse[var]:>7.3f} {m.tvalues[var]:>7.3f} {m.pvalues[var]:>9.4f} {sig:>5}")

# ── 그래프 ───────────────────────────────────────────────────
colors = ['#e74c3c','#3498db','#2ecc71']
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for i, (ax, xv) in enumerate(zip(axes, X_VARS)):
    x = reg[xv]; y = reg[Y_VAR]
    slope, intercept = np.polyfit(x, y, 1)
    xl = np.linspace(x.min(), x.max(), 200)
    ax.scatter(x, y, alpha=0.4, color=colors[i], s=25)
    ax.plot(xl, slope*xl+intercept, color=colors[i], lw=2.5, label=f'beta={slope:.3f}')
    r, p = stats.pearsonr(x, y)
    sig = '***' if p<.001 else '**' if p<.01 else '*' if p<.05 else ''
    ax.set_title(f'{xv} -> {Y_VAR}\nr={r:.3f}{sig}', fontsize=12)
    ax.set_xlabel(xv); ax.set_ylabel(Y_VAR)
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
plt.suptitle(f'회귀분석 기울기 그래프', fontsize=14)
plt.tight_layout()
plt.savefig('회귀_기울기그래프.png', dpi=150, bbox_inches='tight')
print("\n[OK] 회귀_기울기그래프.png 저장")

# 상관관계 히트맵
corr_m = df[LV].corr()
plt.figure(figsize=(9,7))
mask = np.triu(np.ones_like(corr_m, dtype=bool))
sns.heatmap(corr_m, annot=True, fmt='.3f', cmap='RdYlBu_r', mask=mask,
            vmin=-1, vmax=1, annot_kws={'size':10})
plt.title('상관관계 히트맵', fontsize=14)
plt.tight_layout()
plt.savefig('상관관계_히트맵.png', dpi=150, bbox_inches='tight')
print("[OK] 상관관계_히트맵.png 저장")

# 정규분포 그래프
fig, axes = plt.subplots(2, 4, figsize=(20, 8))
axes = axes.flatten()
for i, v in enumerate(LV):
    d = df[v].dropna()
    axes[i].hist(d, bins=12, density=True, color='steelblue', alpha=0.6, edgecolor='white')
    xl = np.linspace(d.min(), d.max(), 200)
    axes[i].plot(xl, stats.norm.pdf(xl, d.mean(), d.std()), 'r-', lw=2)
    axes[i].set_title(f'{v}\nM={d.mean():.2f} SD={d.std():.2f}', fontsize=10)
    axes[i].grid(True, alpha=0.3)
for j in range(i+1, len(axes)): axes[j].set_visible(False)
plt.suptitle('변수별 정규분포', fontsize=14)
plt.tight_layout()
plt.savefig('정규분포_결과.png', dpi=150, bbox_inches='tight')
print("[OK] 정규분포_결과.png 저장")

print("\n===== 분석 완료 =====")
