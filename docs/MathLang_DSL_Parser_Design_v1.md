# MathLang DSLパーサ設計仕様書（v1）

> 本仕様書は、MathLang v1におけるDSL構文 (`problem`, `step`, `end`) を解析するための**Lark構文定義**と、AST出力仕様、およびCoreエンジンとの連携方式を定義する。目的は、教育的ステップ計算を「文法的に」記述可能にし、ASTを通じて意味的評価に接続することである。

---

## 1. 概要

MathLang DSLは、学習者の思考過程（問題提示→途中計算→結果確認）をプログラムとして表現できる、教育向けの簡易数理言語である。

### 記述例
```mathlang
problem: (3 + 5) * 4
step: 8 * 4
end: 32
```

---

## 2. 言語設計の目的

| 項目 | 内容 |
|------|------|
| **目的** | 数学的思考プロセスを構文として明示化する。 |
| **入力** | 教育用DSL (MathLang構文) |
| **出力** | AST構造(JSON) |
| **接続先** | Core Engine (AST評価・知識ノード照合) |

---

## 3. 文法仕様

### 3.1 文法定義（BNF形式）
```
Program      ::= (Statement NEWLINE)*
Statement    ::= ProblemDecl | StepDecl | EndDecl | Comment
ProblemDecl  ::= 'problem' ':' Expr
StepDecl     ::= 'step' ':' Expr
EndDecl      ::= 'end' ':' (Expr | 'done')
Expr         ::= 数式（四則演算, 括弧, 変数, 関数式）
Comment      ::= '#' 任意の文字列
```

### 3.2 Lark構文定義
```python
mathlang_grammar = r"""
?start: statement+

statement: problem | step | end | comment

problem: "problem" ":" expr
step: "step" ":" expr
end: "end" ":" expr | "end" ":" "done"
comment: /#.*/

?expr: term
     | expr "+" term   -> add
     | expr "-" term   -> sub
?term: factor
     | term "*" factor -> mul
     | term "/" factor -> div
?factor: NUMBER        -> number
       | SYMBOL        -> var
       | "(" expr ")"

%import common.CNAME -> SYMBOL
%import common.NUMBER
%import common.WS
%ignore WS
%ignore /\n+/  # 改行を無視
%ignore comment
"""
```

---

## 4. AST出力仕様

### 4.1 構造概要
Larkパーサが生成するASTは、JSON形式でCore Engineに受け渡される。

### 4.2 出力フォーマット
```json
{
  "type": "Program",
  "body": [
    { "type": "ProblemDecl", "expr": "(3 + 5) * 4" },
    { "type": "StepDecl", "expr": "8 * 4" },
    { "type": "EndDecl", "expr": "32" }
  ]
}
```

### 4.3 ASTノード定義
| ノード名 | 属性 | 説明 |
|-----------|------|------|
| `Program` | `body` | ステートメントの配列 |
| `ProblemDecl` | `expr` | 初期式 |
| `StepDecl` | `expr` | 途中計算式 |
| `EndDecl` | `expr` | 結果または`done`キーワード |
| `Expr` | `value` | 四則式・変数・括弧式 |

---

## 5. Core Engine連携

### 5.1 連携フロー
```
MathLang Source
   ↓ (parse)
Lark Parser
   ↓ (emit AST)
Core Engine.load(AST)
   ↓ (evaluate)
Knowledge Node Matching
```

Knowledge Nodeは `docs/knowledge_nodes_spec.md` に定義されたカテゴリ別ファイルを参照し、`MathLang_Core_DSL_v1_spec.md` に沿った式変形を認識する。Core EngineはAST（構文）と知識ノード（意味）を組み合わせ、`problem → step → end` の検証ログへルールIDを記録する。

### 5.2 Engine呼び出し例
```python
from mathlang.parser import parse
from mathlang.core import Engine

ast = parse('''
problem: (3 + 5) * 4
step: 8 * 4
end: 32
''')

engine = Engine(knowledge_base)
engine.load(ast)
engine.run()
```

---

## 6. パーサ拡張方針

### 6.1 拡張構文候補
| 構文 | 説明 |
|------|------|
| `explain:` | 途中計算の理由を自然言語で付与 |
| `ai_step:` | AIによる途中式生成 |
| `compare:` | 学習者とAI出力の照合 |
| `hint:` | 次ステップ提案 |

### 6.2 サンプル
```mathlang
problem: (a + b)^2
ai_step: expand(expr)
step: a^2 + 2ab + b^2
explain: "二項定理を用いました"
end: done
```

---

## 7. AST拡張設計（教育AI対応）

| ノード | 新属性 | 内容 |
|---------|----------|------|
| `StepDecl` | `source` | `user` or `ai` を区別 |
| `ExplainDecl` | `text` | 教師モデルの説明文 |
| `CompareDecl` | `target` | 照合対象ステップID |

---

## 8. エラーハンドリング仕様

| エラー名 | 発生条件 | 処理 |
|-----------|-----------|------|
| `SyntaxError` | 構文誤り | 行番号付きで報告 |
| `UnrecognizedToken` | 不正トークン | ユーザーへ構文候補提示 |
| `InvalidExprError` | 数式解析不能 | SymPy変換時に検出 |

例：
```text
SyntaxError(line 2): 未知のトークン 'step1'。 'step:' を使用してください。
```

---

## 9. 実装テスト仕様

| テスト名 | 入力 | 期待出力 |
|-----------|------|-----------|
| 正常入力 | `problem: 1 + 2` | ASTにProblemDeclノード生成 |
| ステップ連続 | 複数`step:` | 順序を保持したAST配列生成 |
| コメント付き | `# コメント` | コメントノード除外 |
| 構文誤り | `prob: 1 + 2` | SyntaxError発生 |

---

## 10. 開発方針まとめ

- **目的**：教育的数理DSLをAST経由で解析・評価可能にする。  
- **設計理念**：構文（Syntax）と意味（Semantics）を明確に分離。  
- **構成**：Larkパーサ → AST(JSON) → Core Engine → Knowledge Node。  
- **拡張方向**：AI生成ノード（`ai_step`, `explain`）の追加。  

> MathLang DSLパーサは、「数式の読み方を教えるコンパイラ」である。  
> 学習者の思考過程をプログラム構造として捉え、AIが理解・支援可能な形式に変換する。
