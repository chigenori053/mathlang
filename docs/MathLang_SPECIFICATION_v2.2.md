# MathLang Specification v2.2
## Core Architecture — Knowledge-Based Learning DSL

---

## I. 概要
MathLangは「数学的思考の正当性」をコードで検証する学習用DSLである。  
数式の変形プロセスを構文的・論理的に追跡し、各ステップが正当かどうかを  
**KnowledgeRegistry（知識ベース）** に基づいて根拠付きで判定する。

---

## II. コアフロー構成（Core Flow v2.1）

### 全体概要
MathLangのコアフローは、以下の5層構造で構成される：

```
1. Parser           : DSL → AST生成（思考構造の形式化）
2. Normalizer       : ASTの正規化（表記揺れ吸収）
3. Evaluator        : 各stepを比較・同値性検証
4. KnowledgeRegistry: ルール照合と根拠付け
5. Logger           : 推論過程の記録と出力
```

---

### コアフロー図

```
┌────────────────────────────┐
│   DSL Source (problem/prepare/step/end) │
└───────────────┬────────────────┘
                │
        [1] Parser
                ↓
        ProblemNode(AST)
                ↓
        [2] Normalizer
                ↓
        [3] Evaluator
                ↓
        [4] KnowledgeRegistry
                ↓
        [5] Logger
                ↓
        JSON / Notebook Output
```

---

### 各フェーズの詳細

#### 1. Parser（構文解析層）

**入力:** DSL (例: problem ... end)  
**出力:** `ProblemNode`

| DSLセクション | ASTノード | 説明 |
|----------------|------------|------|
| problem | ProblemNode | 問題全体の定義 |
| prepare | PrepareNode | 変数・条件などの設定 |
| step | StepNode | 数式変形ステップ |
| end | (終端) | AST閉鎖 |

**責務:**
- DSL文を構文解析し、論理的階層構造（AST）を生成。
- 各`step`に `(before_expr, after_expr)` のペアを作成。
- 構文エラー時は `InvalidSyntaxError`。

#### DSL構文定義

```
problem <identifier>
    prepare:
        <変数定義式>*
    step:
        <数式変形1>
    step:
        <数式変形2>
    ...
end
```

#### 例
```
problem Pythagoras
    prepare:
        a = 3
        b = 4
    step:
        c^2 = a^2 + b^2
    step:
        c = sqrt(a^2 + b^2)
end
```

---

#### 2. Normalizer（表現正規化層）

**目的:** 構造的に等価な式を同一形式に統一する。

**処理:**
- 可換演算（加法・乗法）の項順序ソート  
- 単位元削除 (`+0`, `×1`)  
- 冗長ネスト解消 (`(a+b)+0 → a+b`)  
- 定数畳み込み (`2+3 → 5`)

**出力:**  
`normalized_before`, `normalized_after`  
同一であれば `rule_id = ARITH-NORM-000` として同値扱い。

---

#### 3. Evaluator（同値性検証層）

**目的:** 各ステップが数学的に妥当かを判定する。

**入力:** ProblemNode  
**処理フロー:**
1. `prepare`を実行して変数環境を構築。
2. 各`step`について：
   - normalize(before/after)
   - 一致 → 自明同値
   - 不一致 → KnowledgeRegistryで照合
3. 一致ルールがあれば `rule_id` を採用
4. 一致なし → `NoSuchRuleError`

**出力:** Stepごとの `EvaluationResult`

---

#### 4. KnowledgeRegistry（知識ルール層）

**目的:** 「なぜ同値なのか」を明示的ルールで説明。

**ルール格納構造**
```
core/knowledge/
  registry.py
  arithmetic/
    addition.yaml
    subtraction.yaml
    multiplication.yaml
    division.yaml
```

**ルール例**
```yaml
- id: ARITH-ADD-001
  name: Commutativity of Addition
  intent: "a + b ≡ b + a"
  pattern_before: "Add(a, b)"
  pattern_after:  "Add(b, a)"
  constraints:
    - "type(a) in [Number, Symbol]"
    - "type(b) in [Number, Symbol]"
```

**API**
```python
match(before_ast, after_ast) -> List[RuleHit]
```

**制約:**  
`prepare`で定義された変数環境を束縛条件として照合可能。

---

#### 5. Logger（思考記録層）

**目的:** 各ステップの推論結果を可視化。

**フォーマット**
```json
{
  "step_idx": 1,
  "before": "Add(a,b)",
  "after": "Add(b,a)",
  "normalized_before": "Add(a,b)",
  "normalized_after": "Add(b,a)",
  "equivalent": true,
  "rule_id": "ARITH-ADD-001",
  "reason": "Commutativity of Addition"
}
```

**出力:** JSON / Notebook形式。  
**用途:** 学習履歴・自動フィードバック。

---

### エラー伝播設計

| 階層 | 例外 | 内容 |
|------|------|------|
| Parser | InvalidSyntaxError | DSL構文エラー |
| Normalizer | InvalidExpression | AST構造不正 |
| Evaluator | NoSuchRule / NonEquivalentStep | 妥当性検証失敗 |
| Registry | AmbiguousRule | 複数ルール一致 |
| Logger | IOError | 出力失敗 |

---

## III. AST構造定義

```python
@dataclass
class ExpressionNode:
    expr: Any

@dataclass
class AssignmentNode:
    name: str
    value: ExpressionNode

@dataclass
class PrepareNode:
    assignments: List[AssignmentNode]

@dataclass
class StepNode:
    before: ExpressionNode
    after: ExpressionNode
    rule_id: Optional[str] = None

@dataclass
class ProblemNode:
    name: str
    prepare: PrepareNode
    steps: List[StepNode]
```

---

## IV. テスト仕様

| テスト項目 | 内容 | 成否条件 |
|-------------|------|----------|
| Parser基本 | problem構文の解析 | ProblemNode生成 |
| Prepare構文 | 変数定義の解析 | AssignmentNode生成 |
| 正規化 | AST整形 | Add(2, Add(0, x)) → Add(2, x) |
| 可換律 | a+b ≡ b+a | rule_id=ARITH-ADD-001 |
| 結合法則 | (a+b)+c ≡ a+(b+c) | rule_id=ARITH-ADD-002 |
| 単位元 | a+0 ≡ a | rule_id=ARITH-ADD-003 |
| 分配法則 | a*(b+c) ≡ a*b+a*c | rule_id=ARITH-MUL-001 |
| 非同値 | a+b ≠ a*b | 例外発生 |
| 曖昧一致 | 複数ルール一致 | AmbiguousRule |
| 不正構文 | a+ | InvalidSyntax |
| 零除算 | a/0 | TypeMismatch |
| 自明同値 | a+(b+c) vs (a+b)+c | ARITH-NORM-000 |

---

## V. DoD（Definition of Done）
✅ Parserが `problem-prepare-step-end` に対応  
✅ KnowledgeRegistryが四則すべてに対応  
✅ Evaluatorがrule_id付きでログ出力  
✅ pytest全12ケース緑  
✅ Core DSL / SPEC文書更新完了  
✅ CIワークフロー組込み済み  

---

## VI. 開発フェーズ優先順位

| フェーズ | コンポーネント | 目的 |
|-----------|----------------|------|
| Phase 1 | Parser / AST | 構文構造確立 |
| Phase 2 | KnowledgeRegistry | 同値根拠付け |
| Phase 3 | Evaluator統合 | ステップ単位検証 |
| Phase 4 | Logger出力 | 思考過程可視化 |

---

## VII. 目的と理念

この「コアフロー構成」はMathLangの心臓部であり、  
DSLを**思考のコード**として解析し、  
各ステップを**ルール根拠付きで検証**する仕組みを形式化する。  

> **要するに：**  
> - Parserが“思考を構造化”し、  
> - Normalizerが“表記差を吸収”し、  
> - Evaluatorが“正当性を判定”し、  
> - KnowledgeRegistryが“根拠を付与”し、  
> - Loggerが“学習過程を記録”する。  

これが **MathLang Core Flow v2.2**。  
数学的推論をコード化し、その正当性を形式的に検証するための完全な流れである。
