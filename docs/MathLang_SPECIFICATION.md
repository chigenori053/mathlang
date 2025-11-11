# 📘 MathLang 開発仕様書（Draft v0.1）

## I. プロジェクト概要

### 1. 名称
**MathLang（Mathematical Thinking Language）**

### 2. 開発目的
数学的思考を「手順（プロセス）」として可視化・記述し、  
人間の**思考過程（working）をAIと共に再構築・検証**する教育支援型プログラミング言語を開発する。

### 3. 開発目標
- 算数・数学の**手計算過程をコード化**できるDSL（Domain-Specific Language）の実現。  
- 論理ステップを**逐次的に実行・表示・比較**できる評価系（Evaluator）の設計。  
- SymbolicAIによる「数式の意味的理解と変形」を支援。

---

## II. 技術アーキテクチャ

### 1. ベース技術スタック
| 分類 | 技術 | 用途 |
|------|------|------|
| 言語基盤 | Python 3.12 (安定版) | メイン実装 |
| 仮想環境 | uv (or venv) | 環境構築・依存管理 |
| AST操作 | `ast` / `lark-parser` | パーサ構築 |
| シンボリック演算 | `sympy` / 独自SymbolicAI | 数式変形・推論 |
| データ管理 | `pandas` | 学習・分析データ管理 |
| UI/教育支援 | `JupyterLab` / `Streamlit` | 対話UI |
| バージョン管理 | `git` / `GitHub` | ソース管理 |
| テスト | `pytest` | 単体・統合テスト |

---

## III. システム構成

### 1. ディレクトリ構造（標準案）

```
mathlang/
├── core/
│   ├── parser.py               # 構文解析器
│   ├── evaluator.py            # 評価器（逐次評価）
│   ├── polynomial.py           # 多項式データ構造と演算
│   ├── polynomial_evaluator.py # 多項式評価器
│   ├── ast_nodes.py            # 文法ノード定義
│   ├── optimizer.py            # AST最適化パス
│   ├── symbolic_engine.py      # SymbolicAI連携
│   └── knowledge/              # カテゴリ別知識ノード（docs/knowledge_nodes_spec.md）
│       └── arithmetic/
│           ├── addition.json
│           ├── subtraction.json
│           ├── multiplication.json
│           └── division.json
├── examples/
│   ├── pythagorean.mlang       # サンプルスクリプト
│   └── run_example.py          # CLIデモヘルパー
├── docs/
│   └── SPECIFICATION.md        # 開発仕様書
├── notebooks/
│   └── Learning_Log_Demo.ipynb   # Jupyterサンプル（LearningLoggerデモ）
├── tests/
│   ├── test_parser.py
│   ├── test_evaluator.py
│   ├── test_cli.py
│   ├── test_symbolic_engine.py
│   └── test_polynomial.py
├── main.py                     # CLIエントリポイント
├── pyproject.toml
└── README.md
```

---

## IV. 言語仕様（MathLang Core DSL v1）

> 詳細仕様は `MathLang_Core_DSL_v1_spec.md` を参照。ここでは開発仕様書向けに要点をまとめる。

### 1. 文法概要
```bnf
Program      ::= (Statement NEWLINE)*
Statement    ::= ProblemDecl | StepDecl | EndDecl | ExplainDecl
ProblemDecl  ::= "problem" ":" Expr
StepDecl     ::= "step" ("[" StepId "]")? ":" Expr
EndDecl      ::= "end" ":" (Expr | "done")
ExplainDecl  ::= "explain" ":" STRING
Expr         ::= 四則演算・括弧・変数・関数式などの数式表現
StepId       ::= 1..n を示す識別子（任意）
```

### 2. コア構文と意味
| 構文 | 役割 | 内部API連携 |
|------|------|-------------|
| `problem: <expr>` | 初期式の宣言。AST生成と初期状態の保存。 | `Engine.set(expr)` |
| `step[:|<id>] <expr>` | 中間計算の提示と同値性検証。 | `Engine.check_step(expr)` |
| `end: <expr|done>` | 最終結果の検証と完了ログ出力。 | `Engine.finalize(expr)` |
| `explain: "..."` | 変形理由などの教育メタ情報。 | ステップログへ注釈を付与 |

### 3. 記述例
```mathlang
problem: (3 + 5) * (2 + 1)
step1: 8 * (2 + 1)
step2: 8 * 3
end: 24
```

ステップ実行時のログイメージ：
```
[problem] (3 + 5) * (2 + 1)
[step1]  8 * (2 + 1)   # addition
[step2]  8 * 3         # multiplication
[end]    24            # done
```

### 4. エラーとバリデーション方針
- `SyntaxError`：構文解析に失敗した場合。  
- `MissingProblemError`：`problem` 前に `step` / `end` が現れた場合。  
- `InvalidStepError`：`step` が直前式と同値でない場合。  
- `InconsistentEndError`：`end` が最後の `step` と一致しない場合。

Evaluatorは各`step`でAST比較・SymbolicAIによる同値性判定を実施し、成功したステップのみが履歴へ記録される。

### 5. 実装・CLIノート
- CLIは `problem → step* → end` の順序を強制し、途中式ログと検証結果を逐次表示する。  
- `--symbolic` 系オプションは `explain` や `ai_step` 拡張（v1では予約語）と連携予定。  
- `examples/*.mlang` はCore DSL v1フォーマットで順次更新する。

---

## V. コンポーネント設計

### 1. Parserクラス設計

```python
class Parser:
    """
    Core DSL (problem / step / end / explain) をASTへ変換する構文解析器。
    行指向の入力を読み取り、ProgramNode配下に ProblemNode → StepNode* → EndNode を構築する。
    """
    def __init__(self, source: str):
        self.lines = source.splitlines()

    def parse(self) -> ProgramNode:
        """
        1. problem宣言を検出し ProblemNode を生成。
        2. 連続する step/step[n] を StepNode として格納（省略可）。
        3. end節と任意の explain節を EndNode/ExplainNode としてまとめる。
        構文違反時は SyntaxError を送出。
        """
        ...
```

### 2. Evaluatorクラス設計

```python
class Evaluator:
    """
    Parserが生成した ProgramNode を逐次評価し、
    Engine(set/check_step/finalize) と連携して同値性検証ログを生成する。
    """
    def __init__(self, program_ast, engine: Engine, *, explain_hook=None):
        self.program_ast = program_ast
        self.engine = engine
        self.explain_hook = explain_hook  # explain節やSymbolicAI注釈の統合ポイント

    def run(self):
        """problem → step* → end の順に各ノードを処理し、検証結果とメタ情報を返す。"""
        ...

    def _handle_step(self, step_node):
        """
        Engine.check_step を呼び出し、同値でなければ InvalidStepError を発生。
        explain_hook があればステップログへ理由を添付する。
        """
        ...
```

### 3. PolynomialEvaluatorクラス設計

```python
class PolynomialEvaluator:
    """
    Core DSLで与えられた problem/step/end を多項式領域で評価。
    各 step の式を正規形に還元し、前ステップとの差分（展開・整理規則）を検証する。
    """
    def __init__(self, program_ast, *, normalizer):
        self.program_ast = program_ast
        self.normalizer = normalizer  # 交換律/結合法則/分配法則を適用する正規化関数

    def run(self):
        """Evaluator同様のフローで、stepごとの正規化結果と差分をログに蓄積する。"""
        ...
```

### 4. SymbolicEngineクラス設計（SymbolicAI連携）

```python
class SymbolicEngine:
    """
    数式構造の意味的解析と変形を司る
    """
    def simplify(self, expr):
        """式の簡約化"""
        ...
    def explain(self, expr):
        """思考的説明生成"""
        ...
```

### 5. KnowledgeRegistry/KnowledgeNode設計

> 詳細スキーマは `docs/knowledge_nodes_spec.md` を参照。

```python
class KnowledgeRegistry:
    """
    core/knowledge/<domain>/<category>.json をロードし、
    Evaluatorが problem/step/end の変形を照合できるようにする。
    """
    def __init__(self, base_path: Path):
        self.nodes = self._load_all()

    def match(self, before: str, after: str) -> KnowledgeNode | None:
        """式テンプレートとカテゴリから候補ルールを返す。"""
        ...
```

- **カテゴリ分割**：四則演算ごとにファイルを分割（`arithmetic/addition.yaml` など）し、必要に応じて `advanced/exponent.yaml` などを追加する。  
- **ルールID**：`<DOMAIN>-<CATEGORY>-<連番>`（例: `ARITH-ADD-001`）。  
- **Evaluator連携**：Core DSLステップのスナップショットを KnowledgeRegistry に照会し、同値検証ログへルールID/説明を付与する。

---

## VI. 実装フェーズ計画

| フェーズ | 内容 | 期間 |
|-----------|------|------|
| Phase 1 | Parser/Evaluator基盤開発 | 〜2025年11月中旬 |
| Phase 2 | SymbolicAI連携・AST最適化 | 〜12月初旬 |
| Phase 3 | Jupyter UI & 学習ログ機能 | 〜12月下旬 |
| Phase 4 | 教育実験版リリース（v0.9） | 2026年1月予定 |

---

## VII. 開発ポリシー

1. **教育的透明性**：演算結果よりも「途中経過」を重視。  
2. **AI連携性**：SymbolicAIによる「なぜその式になるか」を説明。  
3. **再現性**：同じ入力は同じプロセスを再現可能。  
4. **軽量・拡張性**：Pythonベースで教育環境・研究用途どちらにも展開可能。

---

## VIII. 将来的拡張

| 機能 | 概要 |
|------|------|
| 証明モジュール | 数学的証明のステップ推論 |
| 教師用ログ出力 | 学習者の思考履歴分析 |
| 自然言語理解 | 数式⇄文章相互変換 |
| Web IDE統合 | 教育用プラットフォーム統合 |

---

## IX. GitHub運用ルール（初期案）

- main: 安定版
- dev: 開発ブランチ
- feature/*: 機能別ブランチ  
- PR: コードレビュー必須
- commit規約例：`feat(parser): implement expression parsing`

---

## X. 環境構築手順（macOS向け）

```bash
# プロジェクト作成
mkdir mathlang && cd mathlang

# 仮想環境作成 (uv)
uv init
uv python install 3.12
uv venv

# 依存パッケージ
uv add sympy lark-parser jupyter pytest

# GitHub 初期化
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:<username>/mathlang.git
git push -u origin main
```

---

## XI. リリースチェックリスト（ドラフト）

- [ ] Parser/Evaluatorのテスト (`pytest`) が緑であること。
- [ ] `main.py` のCLI仕様と `README.md`/本仕様書の手順が一致していること。
- [ ] `examples/` 配下のスクリプト（`pythagorean.mlang` と `run_example.py`）がそのまま実行できること。
- [ ] CLIの`--symbolic`モードが動作し、SymPy依存や出力仕様に変更があればREADME/仕様書へ反映すること。
- [ ] CLIの`--symbolic-trace`モードが動作し、SymPy依存や出力仕様に変更があればREADME/仕様書へ反映すること。
- [ ] CLIの`--hello-world-test`が想定どおりのステップ／出力を示すこと。
- [ ] CLIの`--language`がja/enを切り替え、ステップ／出力表記が対応すること。
- [ ] CLIやディレクトリ構造に変更があれば、同時に計画シートとリリースノート草案へ反映すること。

---

## XII. 参考文献・理論的根拠

- Bruner, J. S. *The Process of Education* (1960)
- Papert, S. *Mindstorms: Children, Computers, and Powerful Ideas* (1980)
- Larkin, J. & Simon, H. *Why a Diagram is (Sometimes) Worth Ten Thousand Words* (1987)
- 日本教育工学会: 「数理的思考過程の可視化研究」(2021)
-### 6. LearningLogger設計

```python
class LearningLogger:
    """
    Evaluator/PolynomialEvaluatorから呼ばれ、stepごとの記録をJSONとして蓄積する。
    """
    def record(self, *, phase: str, expression: str, rendered: str, status: str, rule_id: str | None = None):
        ...

    def to_dict(self) -> list[dict[str, Any]]:
        ...
    def write(self, path: Path): ...
```

- `Evaluator` / `PolynomialEvaluator` コンストラクタに `learning_logger` を渡すと、`problem`, `step`, `end`, `explain`, `show`, `assignment` など各イベントを `LearningLogger` が受け取り、`rule_id`（知識ノードID）や `status`（同値判定、info等）を含むJSONとして保持する。  
- Jupyterデモは `notebooks/Learning_Log_Demo.ipynb` に配置し、Core DSL スニペルを走らせながらログを可視化する。
