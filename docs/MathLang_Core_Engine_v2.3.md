# MathLang Core Engine Design v2.3
## Arithmetic + Fraction Extended Specification  
**四則計算エンジンの完全化 + 分数計算エンジンの正式統合**

---

# I. 概要

MathLang Core Engine v2.3 は、  
**「整数/実数の四則演算」** と **「分数（有理数）計算」** を明確に分離した二層構造アーキテクチャである。

本仕様書では：

1. ArithmeticEngine（整数/実数）
2. FractionEngine（分数・有理数）
3. KnowledgeRegistry（ARITH-* / FRAC-*）
4. Evaluator のエンジン選択ロジック
5. AST 拡張（RationalNode）
6. 正規化ポリシー（整数/実数・分数）

を正式に定義する。

---

# II. Core Architecture Overview

```
DSL → Parser → AST
        ↓
    Evaluator
    ├─ ArithmeticEngine   （整数・実数の四則）
    └─ FractionEngine     （有理数・分数）
        ↓
   KnowledgeRegistry
        ↓
      Logger
```

---

# III. AST Design

## 3.1 ExpressionNode

```
@dataclass
class ExpressionNode:
    expr: Any
```

## 3.2 RationalNode（新規）

```
@dataclass
class RationalNode(ExpressionNode):
    numerator: ExpressionNode
    denominator: ExpressionNode
```

### RationalNode の使用基準

| DSL | AST | Engine |
|-----|-----|--------|
| `1/2` | RationalNode(1,2) | FractionEngine |
| `a/b` | RationalNode(a,b) | FractionEngine |
| `a / 2`（割り算） | Div(a,2) | ArithmeticEngine |

---

# IV. Evaluator Specification

Evaluator は式に RationalNode を含むかでエンジンを切り替える。

```
def contains_rational(ast): ...
def choose_engine(ast):
    return FractionEngine if contains_rational(ast) else ArithmeticEngine
```

Evaluator の処理手順は：

1. prepare の変数を展開  
2. before/after を正規化  
3. エンジン選択  
4. KnowledgeRegistry で rule_id を取得  
5. Logger に記録  

---

# V. ArithmeticEngine（整数/実数）

## 5.1 Normalizer（整数/実数）

- Add/Mul のソート  
- `+0` / `*1` の削除  
- `a*0 → 0`  
- `-(-a) → a`  
- 定数畳み込み：`2+3=5`, `2*3=6`

## 5.2 Arithmetic KB（ARITH-*）

### Addition
- ARITH-ADD-001 可換律  
- ARITH-ADD-002 結合律  
- ARITH-ADD-003 単位元  
- ARITH-ADD-004 加法逆元  

### Subtraction
- ARITH-SUB-001 `a - b = a + (-b)`  
- ARITH-SUB-002 減法正規形  

### Multiplication
- ARITH-MUL-001 可換律  
- ARITH-MUL-002 結合律  
- ARITH-MUL-003 単位元  
- ARITH-MUL-004 零元  
- ARITH-MUL-005 符号規則  

### Division
- ARITH-DIV-001 `a/b = a*(1/b)`  
- ARITH-DIV-002 `a/1 = a`  
- ARITH-DIV-003 逆元  

---

# VI. FractionEngine（分数）

## 6.1 Normalization ポリシー

1. 分子・分母を ArithmeticEngine の Normalizer に通す  
2. 約分：`2/4 → 1/2`  
3. 符号整理：  
   - `a/-b → -a/b`  
   - `-a/-b → a/b`  

## 6.2 Fraction KB（FRAC-*）

### Fraction Addition

```
- id: FRAC-ADD-001
  name: Fraction addition
  intent: "(a/b) + (c/d) ≡ (ad + bc) / bd"
  pattern_before: "Add(Rational(a,b), Rational(c,d))"
  pattern_after: "Rational(Add(Mul(a,d), Mul(b,c)), Mul(b,d))"
```

### Fraction Multiplication

```
- id: FRAC-MUL-001
  intent: "(a/b)*(c/d) ≡ (ac)/(bd)"
```

### Fraction Division

```
- id: FRAC-DIV-001
  intent: "(a/b)/(c/d) ≡ (a*d)/(b*c)"
```

### Reduction

```
- id: FRAC-NORM-001
  intent: "(a*k)/(b*k) ≡ a/b"
```

---

# VII. KnowledgeRegistry v2.3

## ルールパス

```
core/knowledge/arithmetic/*.yaml
core/knowledge/fraction/*.yaml
```

## match API

```
match(before, after, domain="arith" or "fraction")
```

---

# VIII. 統合フロー

```
Parser → AST
   ↓
Evaluator
   ↓ choose_engine
ArithmeticEngine / FractionEngine
   ↓
KnowledgeRegistry
   ↓
Logger
```

---

# IX. Logger Format

```
{
  "step_idx": 1,
  "before": "Add(Rational(1,2), Rational(1,3))",
  "after": "Rational(5,6)",
  "equivalent": true,
  "rule_id": "FRAC-ADD-001"
}
```

---

# X. テスト仕様

## ArithmeticEngine
- a+b ≡ b+a  
- (a+b)+c ≡ a+(b+c)  
- a+0=a  
- a*1=a  
- a*0=0  
- a-b=a+(-b)  

## FractionEngine
- 1/2 + 1/3 = 5/6  
- 2/4 = 1/2  
- (a/b)*(c/d) = ac/bd  
- (a/b)/(c/d) = ad/bc  
- 符号正規化  

---

# XI. DoD

- 全 ARITH-* ルールが動作  
- 全 FRAC-* ルールが動作  
- Evaluator がエンジン切替  
- Logging が rule_id 付きで出力  
- 全テスト緑  

---

# XII. 結論

MathLang Core Engine v2.3 は：

- 四則演算の完全性
- 分数（有理数）演算の完全性
- rule_id による根拠付け
- AST/Engine/KB の責務分離

を備えた、MathLang の中核エンジンである。
