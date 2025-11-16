# MathLang Task Management Sheet v2.2
## Focus: Core Architecture Demo Release (Reasoning + Causal)

---

| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-01 | ルール/曖昧判定の本番データ化 | KnowledgeRegistry/FuzzyJudge の実データ検証・精度チェック | Day11 | ☑ |
| CORE-02 | カウンターファクトシナリオ整備 | 代表的な介入シナリオのDSLサンプル＋CLIオプション拡張 | Day12 | ☑ |
| CORE-03 | 因果グラフ可視化 | graph_to_text/dot をNotebook/CLIデモに統合 | Day13 | ☑ |
| CORE-04 | デモパッケージ | CLI/Notebookのサンプルスクリプトと説明資料を整備 | Day13 | ☑ |
| CORE-05 | ドキュメント更新 | README / Spec / Test Plan をデモ版仕様へ同期 | Day13 | ☑ |
| OPS-01 | 文書同期ツール | make doc-sync / validate rule IDs | Day7 | ☑ |
| OPS-02 | CI監視 | pytest 50件 + lint のCI連携確認 | Day13 | ▢ |

---

### 完了タスク
- CORE-01: 実データ（`docs/data/fuzzy_samples.json`）を用いた KnowledgeRegistry/FuzzyJudge の検証
- CORE-02: `edu/examples/counterfactual_demo.mlang` ＋ CLI `--counterfactual` による介入デモ
- CORE-03: `graph_to_text/dot` を CLI / Notebook デモに統合
- CORE-04: `docs/demo/counterfactual_walkthrough.md` などデモ資料整備
- CORE-05: README / Spec / Test Plan などドキュメント同期
- OPS-01: 文書同期ツール

未完タスク: OPS-02 (CI監視の自動化)

---

### 廃止／凍結タスク
| ID | 内容 | 理由 |
|----|------|------|
| EXT-01 | 微分・行列拡張 | デモ版スコープ外 |
| DOC-02 | 日本語UIガイド | Coreデモ完成後に再開 |

---

### 成功基準
- Reasoningログに `rule_id` / `status` / 因果解析を表示  
- 代表的な MathLang プログラム（CLI + Notebook）が Fuzzy/因果/カウンターファクトを一括体験  
- `run_causal_analysis` + `graph_to_*` を用いた可視化デモを提供  
- pytest 50件 + デモシナリオの手動チェックが緑  
- README / Spec / Test Plan がデモ版のワークフローを説明  
- CIでCLI/Notebookデモの self-test を実行（Hello World + causal sample）  

---

### コメント
> Core reasoning + causal のアーキテクチャは完成。  
> ここからは「体験」重視のデモ構築に集中：本番データでの判定精度、介入シナリオのテンプレ化、Notebook/CLIでの可視化を揃える。  
> 50件の自動テスト + デモ手順を公開し、学習ログ→因果分析→カウンターファクトまでをワンストップで確認できる状態を目指す。唯一の未了タスクは OPS-02 (CI監視)。

---

### サマリー
- Python 3.12 / 3.14 で 50 件の pytest が成功。CLI/Evaluator/Fuzzy/Fraction/Polynomial/Symbolic/CausalEngine まで網羅。
- CLI ではエラー時に因果サマリを自動表示し、`--counterfactual` 指定でシミュレーション結果も出力。Notebook では `run_causal_analysis` + `graph_to_text/dot` で可視化可能。
- カウンターファクト API は複数介入・再実行ログまで提供済み。`docs/demo/counterfactual_walkthrough.md` でデモ手順を提供。
- `docs/test_plan_reasoning.md` でテストシナリオを整理済み。デモ版完成のため、CORE-01〜05タスクを優先し、不要タスクは整理済み。
