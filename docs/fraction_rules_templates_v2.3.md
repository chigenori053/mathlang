# Fraction Rules YAML Templates (FRAC-*)

## 1. Addition

```yaml
- id: FRAC-ADD-001
  name: Fraction addition (common denominator)
  intent: "(a/b) + (c/d) ≡ (ad + bc) / bd"
  pattern_before: "Add(Rational(a,b), Rational(c,d))"
  pattern_after:  "Rational(Add(Mul(a,d), Mul(b,c)), Mul(b,d))"
  constraints:
    - "b != 0"
    - "d != 0"
```

## 2. Multiplication

```yaml
- id: FRAC-MUL-001
  name: Fraction multiplication
  intent: "(a/b) * (c/d) ≡ (ac) / (bd)"
  pattern_before: "Mul(Rational(a,b), Rational(c,d))"
  pattern_after:  "Rational(Mul(a,c), Mul(b,d))"
```

## 3. Division

```yaml
- id: FRAC-DIV-001
  name: Fraction division
  intent: "(a/b) / (c/d) ≡ (a*d) / (b*c)"
  pattern_before: "Div(Rational(a,b), Rational(c,d))"
  pattern_after:  "Rational(Mul(a,d), Mul(b,c))"
  constraints:
    - "b != 0"
    - "c != 0"
    - "d != 0"
```

## 4. Reduction (約分)

```yaml
- id: FRAC-NORM-001
  name: Fraction reduction
  intent: "(a*k)/(b*k) ≡ a/b"
  pattern_before: "Rational(Mul(a,k), Mul(b,k))"
  pattern_after:  "Rational(a,b)"
  constraints:
    - "k != 0"
```
