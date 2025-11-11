# MathLang 知識ノード仕様（v1）

> MathLang Core DSL v1（`MathLang_Core_DSL_v1_spec.md`）に準拠し、`problem → step* → end` の各式を意味的に検証するための「知識ノード(Knowledge Node)」を定義する。知識ノードは Core Evaluator／Polynomial Evaluator から参照され、式変形の判定根拠をカテゴリ単位で管理する。

---

## 1. 目的と適用範囲
- Core DSLの各`step`で実施する「意味的同値判定」に必要なルールを外部化し、AST/シンボリック判定の補助情報として利用する。  
- 四則演算（加減乗除）やべき乗など、教育カリキュラム単位で段階的に知識ノードを拡張できるようにする。  
- ルールセットは JSON/YAML で記述し、テキストレビューとユニットテストの両方で検証可能な粒度を保つ。

---

## 2. ディレクトリ構成

```
core/
└── knowledge/
    ├── arithmetic/
    │   ├── addition.json
    │   ├── subtraction.json
    │   ├── multiplication.json
    │   └── division.json
    └── advanced/
        ├── exponent.yaml
        └── factoring.yaml
```

### ルール
1. ルートは `core/knowledge/`。  
2. サブディレクトリはドメイン（`arithmetic`, `advanced`, `calculus` など）を表す。  
3. 各ファイルはカテゴリ単位（`addition.json` 等）で分割し、同一カテゴリ内に複数のノードを配列で列挙する。  
4. 将来的に微積や行列などを追加する際も、このディレクトリ規約を踏襲する。

---

## 3. ファイルフォーマット

YAML（またはJSON）で下記スキーマを満たす。現在の実装では `.json` を採用。

```json
[
  {
    "id": "ARITH-ADD-001",
    "category": "arithmetic.addition",
    "title": "Combine like terms",
    "pattern": {
      "before": "(a + b) + (c + d)",
      "after": "a + b + c + d"
    },
    "constraints": ["Variables must be commutative symbols."],
    "explanation": "展開後に同類項をまとめる標準手順。",
    "examples": [
      {
        "problem": "(3 + 5) + 2",
        "step": "3 + 5 + 2",
        "end": "10"
      }
    ]
  }
]
```

### フィールド説明
| フィールド | 必須 | 説明 |
|-----------|------|------|
| `id` | ✅ | ルールID（`<DOMAIN>-<CATEGORY>-<番号>`） |
| `category` | ✅ | `arithmetic.addition` など、ディレクトリと一致するパス |
| `title` | ✅ | ルールの短い説明 |
| `pattern.before/after` | ✅ | ルール適用前後の式テンプレート（SymPy互換文字列） |
| `constraints` | 任意 | 制約条件（文字列配列） |
| `explanation` | 任意 | 教育的説明文 |
| `examples` | 任意 | Core DSLサンプル。`problem/step/end` 各式を含める |

---

## 4. カテゴリ分割ポリシー

| カテゴリ | 目的 | サンプルID |
|----------|------|------------|
| `arithmetic.addition` | 同類項結合・交換律 | `ARITH-ADD-00x` |
| `arithmetic.subtraction` | 減法と符号反転 | `ARITH-SUB-00x` |
| `arithmetic.multiplication` | 乗法・分配法則 | `ARITH-MUL-00x` |
| `arithmetic.division` | 除法・約分 | `ARITH-DIV-00x` |
| `advanced.exponent` | べき乗展開 | `ADV-EXP-00x` |
| `advanced.factoring` | 因数分解 | `ADV-FAC-00x` |

> **追加ルール**: 既存カテゴリで表現できないトピックを導入する際は、`docs/knowledge_nodes_spec.md`を更新し、ディレクトリ新設＋ルールIDプレフィックスを定義すること。

---

## 5. Coreアーキテクチャ連携
1. Evaluator/PolynomialEvaluatorは `core/knowledge/` からカテゴリ別ルールをロードし、Core DSLステップを判定する。  
2. ルールは `MathLang_Core_DSL_v1_spec.md` の `problem → step → end` で提示される式変形と1対1で対応させる。  
3. ルール追加時は以下をセットで行う：  
   - 知識ノードファイル編集（カテゴリ別）  
   - 対応する `.mlang` サンプル or `pytest` シナリオの追加  
   - 仕様書 (`MathLang_SPECIFICATION.md`) とタスク管理の更新

---

## 6. 品質保証
- **検証**: `tests/test_evaluator.py` および `tests/test_polynomial.py` に、該当カテゴリのルールを用いたケースを追加する。  
- **レビュー**: ルールID単位でコードレビューを行い、教育的説明とAST整合性を確認する。  
- **バージョニング**: ルールファイルはGitで管理し、変更点はReleaseノートに記載する。

---

## 7. 今後の拡張
- ルール間の依存関係グラフ化（ prerequisite → successor ）。  
- 学年や学習テーマ別のタグ付け。  
- ルール自体をDSL化し、ユーザーが拡張できる仕組みの検討。

> この仕様は Phase 2 の「SymbolicAI/知識ベース」タスクで初回導入を行い、Phase 3 以降の教材化・UI拡張で再利用する。
