# MathLang Integrated Architecture Specification  
**MathLang 統合設計書 v0.0（拡張版）**

# MathLang Integrated Architecture Specification  
**MathLang 統合設計書 v0.0（拡張版）**

> 本書は MathLang プロジェクトにおける **初期統合アーキテクチャ** をまとめた設計書である。  
> DSL → Parser → Evaluator → Engine → SymbolicEngine（厳密）/Fuzzy Reasoning Engine（曖昧）  
> という一貫したパイプラインにより、数学的ステップを「解答」ではなく「思考過程」として扱うことを目的とする。

---

## 目次

1. MathLang 概要  
2. 全体アーキテクチャ構成  
3. DSL 言語仕様 v0.1  
4. コアコンポーネント一覧  
5. Parser 仕様  
6. Evaluator 仕様  
7. Engine 仕様  
8. SymbolicEngine（厳密論理エンジン）仕様  
9. Fuzzy Reasoning Engine（曖昧推論エンジン）仕様  
10. Rule Engine（四則・分数・シンボリック処理）仕様  
11. 学習ログ（LearningLogger）仕様  
12. 設定ファイル（Config）仕様  
13. CLI / ディレクトリ構造  
14. テスト戦略  
15. 拡張ロードマップ (v1.0 以降)  

---

## 1. MathLang 概要

### 1.1 目的

MathLang は、以下を実現することを目的とした **数学学習・研究向けのプログラミング言語 + 推論エンジン** である：

- **数式の「答え」ではなく「思考のステップ」を扱う**  
- 厳密な数学的同値（SymbolicEngine）と、人間らしい「近さ」の判断（Fuzzy Reasoning Engine）を統合  
- 学習者の解法ステップや研究者の記号計算手順を、プログラムとして記述・検証可能にする  

### 1.2 コアコンセプト

- **Step-based**: `problem → step → step → ... → end` というステップ単位で解法を記述する DSL  
- **Two Engines**:  
  - `SymbolicEngine`: T=0 の厳密論理（数式同値）  
  - `Fuzzy Reasoning Engine`: T>0 の曖昧推論（類似度スコアとラベル）  
- **Explainable**: 各ステップは `explain:` によって自然言語説明を付与できる  

---

## 2. 全体アーキテクチャ構成

### 2.1 高レベル構成図

┌────────────────────┐
│ DSL (input) │
│ .mlang ファイル │
└───────────┬────────┘
▼
┌────────────────────┐
│ Parser │
│ DSL → AST (構文木) │
└───────────┬────────┘
▼
┌─────────────────────────────┐
│ Evaluator │
│ problem → step → ... → end │
└──────────┬───────────┬──────┘
▼ ▼
┌────────────────┐ ┌────────────────────┐
│ SymbolicEngine │ │ Fuzzy Reasoning │
│ （厳密論理） │ │ Engine（曖昧推論） │
└────────────────┘ └─────────┬──────────┘
▼
┌───────────────┐
│ Rule Engine │
└───────┬───────┘
▼
┌────────────────┐
│ LearningLogger │
└────────────────┘
