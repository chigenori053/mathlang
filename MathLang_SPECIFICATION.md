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
│   ├── parser.py          # 構文解析器
│   ├── evaluator.py       # 評価器（逐次評価）
│   ├── ast_nodes.py       # 文法ノード定義
│   ├── optimizer.py       # AST最適化パス
│   └── symbolic_engine.py # SymbolicAI連携
├── examples/
│   ├── pythagorean.mlang  # サンプルスクリプト
│   └── run_example.py     # CLIデモヘルパー
├── docs/
│   └── SPECIFICATION.md   # 開発仕様書
├── tests/
│   ├── test_parser.py
│   └── test_evaluator.py
├── main.py                # CLIエントリポイント
├── pyproject.toml
└── README.md
```

---

## IV. 言語仕様（MathLang DSL）

### 1. 文法概要
```bnf
<program>    ::= <statement>+
<statement>  ::= <assign> | <expression> | <explain>
<assign>     ::= <identifier> "=" <expression>
<expression> ::= <term> | <term> <operator> <term>
<explain>    ::= "show" <identifier>
<term>       ::= <number> | <identifier> | "(" <expression> ")"
<operator>   ::= "+" | "-" | "*" | "/" | "^"
```

### 2. サンプルコード
```mathlang
# MathLang Example: Stepwise Computation
a = 2
b = 3
c = a^2 + b^2
show c
```

出力例：
```
Step 1: a = 2
Step 2: b = 3
Step 3: c = a^2 + b^2 → 13
Output: 13
```

### 3. 実行方法（CLI）
| 用途 | コマンド | 備考 |
|------|----------|------|
| ファイルを実行 | `python main.py examples/pythagorean.mlang` | Evaluatorステップ＋Output表示 |
| インラインスニペット | `python main.py -c "a = 2\nb = 3\nshow a + b"` | 文字列に改行を含められる |
| デモ再生 | `python examples/run_example.py` | `examples/`配下サンプルの簡易ランナー |
| シンボリック分析 | `python main.py --symbolic "(a + b)^2 - (a^2 + 2ab + b^2)"` | SymPy必須。簡約結果・説明・構文木を表示 |
| シンボリックトレース付き実行 | `python main.py --symbolic-trace examples/pythagorean.mlang` | DSL評価と同時に`show`出力へ簡約・説明・構文木を付与 |
| Hello World自己診断 | `python main.py --hello-world-test` | CLIが正常ならHello WorldのStep/Outputが表示される |

CLIはEvaluatorのログをそのままターミナルへ出力し、例外時は`[Parse Error]`または`[Evaluation Error]`で標準エラーに通知する。

---

## V. コンポーネント設計

### 1. Parserクラス設計

```python
class Parser:
    """
    数学的表現をASTに変換する構文解析クラス
    """
    def __init__(self, source: str):
        self.source = source

    def parse(self) -> ASTNode:
        """トークン列を解析しASTを生成"""
        ...
```

### 2. Evaluatorクラス設計

```python
class Evaluator:
    """
    ASTを逐次評価し、思考過程を可視化
    """
    def __init__(self, ast_root):
        self.context = {}
        self.ast_root = ast_root

    def step_eval(self):
        """1ステップごとに評価し、プロセスを出力"""
        ...

    def __init__(self, ast_root, symbolic_engine_factory=None):
        """symbolic_engine_factory を与えると show 出力へシンボリック説明を付加"""
        ...
```

### 3. SymbolicEngineクラス設計（SymbolicAI連携）

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
- [ ] CLIの`--hello-world-test`が想定どおりのStep/Outputを示すこと。
- [ ] CLIやディレクトリ構造に変更があれば、同時に計画シートとリリースノート草案へ反映すること。

---

## XII. 参考文献・理論的根拠

- Bruner, J. S. *The Process of Education* (1960)
- Papert, S. *Mindstorms: Children, Computers, and Powerful Ideas* (1980)
- Larkin, J. & Simon, H. *Why a Diagram is (Sometimes) Worth Ten Thousand Words* (1987)
- 日本教育工学会: 「数理的思考過程の可視化研究」(2021)
