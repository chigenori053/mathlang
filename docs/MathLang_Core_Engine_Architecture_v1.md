# MathLang Coreエンジンアーキテクチャ設計仕様書（v1）

> 本仕様書は、MathLangのコアエンジンを構成する2層構造  
> 「構文に忠実なシンプルAST」と「定理/公理をAST変換ルールとして実装したルールエンジン」  
> に基づくアーキテクチャ設計を定義する。

---

## 1. 概要

MathLang Coreエンジンは、**構文解析と意味的変換を完全分離**する教育指向の設計である。

| 層 | 役割 | 概要 |
|----|------|------|
| **Simple AST** | 構文に忠実な抽象構文木 | 数学式を構文レベルで正確に表現 |
| **Rule Engine** | 定理・公理に基づく変換ロジック | ASTをルールに従って書き換える |

この分離により、**教育的説明可能性**と**拡張性**（ルール差し替え）を両立する。

---

## 2. アーキテクチャ全体構成

```
┌──────────────┐    ┌────────────────────────┐
│ Parser/Front  │──▶│ Simple AST (Syntax-faithful) │
└──────────────┘    └──────────┬─────────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │  Rewrite Engine   │  ← 変換ルール（定理/公理）
                      │  (Rule Runner)    │
                      └────────┬──────────┘
                               │
                ┌──────────────┴───────────────┐
                ▼                                ▼
        ┌────────────┐                   ┌──────────────┐
        │ Strategy    │                   │ Normalizer   │
        │ (innermost/ │                   │ (正規形化)   │
        │  outermost) │                   └──────────────┘
        └─────────────┘
                               │
                               ▼
                      ┌───────────────────┐
                      │ Step Log / Trace  │  ← どのルールをどの部分に適用したか
                      │ (provenance)      │
                      └───────────────────┘
```

---

## 3. データモデル

### 3.1 AST定義

```ts
type Expr =
  | Int { value: bigint }
  | Rat { p: bigint, q: bigint }
  | Sym { name: string }
  | Add { terms: Expr[] }
  | Mul { factors: Expr[] }
  | Pow { base: Expr, exp: Expr }
  | Neg { expr: Expr }
  | Call { name: string, args: Expr[] };
```

> 特徴:  
> - 構文に忠実（Add/Mulなどを平坦化せず保持）  
> - 教育的表示において入力式と同一構造を保つ  

---

### 3.2 変換ルール（定理/公理）

```ts
type Rule = {
  id: string;
  pattern: Pattern;
  replace: Template;
  guard?: Guard;
  priority?: number;
  tags?: string[];
  explain?: string;
  reversible?: boolean;
};
```

#### JSON表現例
```json
{
  "id": "BINOMIAL_EXPAND",
  "pattern": { "Pow": [ { "Add": ["$a","$b"] }, { "Int": 2 } ] },
  "replace": { "Add": [
    { "Pow": ["$a", {"Int":2}] },
    { "Mul": [{"Int":2}, "$a", "$b"] },
    { "Pow": ["$b", {"Int":2}] }
  ] },
  "guard": "True",
  "meta": { "explain": "(a+b)^2 = a^2 + 2ab + b^2", "reversible": true }
}
```

---

## 4. ルール適用戦略（戦術制御）

| 戦略名 | 説明 |
|---------|------|
| **innermost** | 内側（葉）から適用。基本モード。 |
| **outermost** | 外側から適用。教育用に明快。 |
| **focus(path)** | 指定ノードにのみ適用。UI連携用。 |
| **normalize** | 毎ステップ後に正規形へ。 |

### 戦略要素
1. 優先度（priority）  
2. 停止性（上限ステップ / サイズガード）  
3. 合流性（同一正規形へ収束するルール集合のみ）  

---

## 5. Core Engine API

```ts
interface Engine {
  set(expr: Expr): void;
  apply(ruleId: string, focus?: Path): Step;
  stepOnce(strategy?: Strategy): Step | null;
  run(maxSteps?: number): Step[];
  isEquiv(a: Expr, b: Expr): boolean;
  normalize(e: Expr): Expr;
  getTrace(): Step[];
}
```

### Step構造
```ts
type Step = {
  before: Expr;
  after: Expr;
  ruleId: string;
  focus: Path;
  guardInfo?: string;
  explain?: string;
};
```

---

## 6. Normalizer（正規形化ポリシー）

| 処理 | 内容 |
|------|------|
| **CAN_FLAT** | Add/Mulの平坦化 |
| **CAN_SORT** | 可換順序のソート |
| **RAT_REDUCE** | 既約分数化 |
| **POW_CANON** | 指数の統一形 |

> normalize(normalize(e)) == normalize(e) を保証すること。

---

## 7. 教育向け制御ポリシー

| 制御項目 | 内容 |
|-----------|------|
| **1ステップ＝1ルール** | 学習UI上での説明単位 |
| **ルール適用ログ** | ruleId, path, before, after, explain を保存 |
| **モード別ルールセット** | “展開”モード, “因数分解”モードを分離 |
| **停止性保護** | 展開と因数分解の同時自動適用は禁止 |

---

## 8. 拡張インターフェース

| 機能 | 説明 |
|------|------|
| **幾何拡張** | `Call("area",[Triangle(A,B,C)])` のように拡張 |
| **方程式操作** | `Eq(left, right)` ノード追加で同値変形可能 |
| **単位処理** | `Quantity(value, unit)` ノードと変換ルール |

---

## 9. テスト戦略

| テスト種別 | 内容 |
|-------------|------|
| **ユニットテスト** | 各ルールの双方向変換 (pattern ⇄ replace) |
| **正規形テスト** | normalizeが冪等であることの確認 |
| **合流性テスト** | 異なる戦略でも同一正規形になるか |
| **教育回帰テスト** | 1手=1説明が成立するか |
| **性能テスト** | 高校レベル式で1手20ms以内 |

---

## 10. 実装ロードマップ

| フェーズ | 内容 |
|-----------|------|
| v1 | Simple AST + 基本ルールエンジン (四則演算, 展開, 因数分解) |
| v1.1 | Normalizer + ルールログ出力 |
| v1.5 | 幾何・単位対応のAST拡張 |
| v2 | e-graphベースの同値探索 (AI推論補完) |

---

## 11. 設計上の決定事項

1. **正規形の定義**：Add/Mulのソート順・係数位置・既約条件を固定。  
2. **戦略のデフォルト**：`innermost`。教育UIでは `focus(path)`。  
3. **ルールメタ情報**：priority, reversible, explain, tagsを保持。  
4. **停止性ガード**：ステップ上限・式サイズ上限を設定。  
5. **トレース必須**：ruleId, path, before/afterを常に記録。

---

## 12. 教育的価値

> 「構文忠実AST × 公理的ルールエンジン」は、  
> 数式を“どう書くか”と“なぜそう変形できるか”を明確に分離する。  
> これにより、学習者は**構文理解 → 意味理解 → 定理応用**という3段階思考を体験できる。

---

## 13. 次アクション

1. 正規形仕様書を作成。  
2. Rule JSONスキーマを確定。  
3. 最小ルールセット10本を実装。  
4. Engine API (`apply`, `normalize`, `trace`) の試作実装。  
5. 教育回帰テストで 1手=1説明 の整合を確認。

---

> MathLang Core Engine は、  
> **教育的説明可能性を持つ最小シンボリック推論システム**として、  
> 数学的思考を形式的・透明に扱う基盤となる。  
