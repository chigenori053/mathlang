# Normalizer Design v2.3
## ArithmeticEngine Normalizer + FractionEngine Normalizer

---

# 1. Arithmetic Normalization

### 規則一覧
- Add / Mul の項のソート
- 単位元の削除 (`+0`, `*1`)
- 零元 (`a*0 → 0`)
- 符号の整理 (`-(-a) → a`)
- 定数畳み込み (`2+3=5`, `2*3=6`)

---

# 2. Fraction Normalization

### RationalNode に対して

1. 分子・分母を ArithmeticEngine の正規化に通す  
2. 約分（2/4 → 1/2）
3. 符号の統一（分母を正にする）
4. 共通因子除去  
   ```
   Rational(a*k, b*k) → Rational(a, b)
   ```

### FractionEngine 正規化ルールID
- `FRAC-NORM-000`: 自明同値  
- `FRAC-NORM-001`: 約分による同値  
