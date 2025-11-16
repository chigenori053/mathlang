# Development Report

## 概要
- CLI/Notebook から因果推論・カウンターファクトを体験できるデモフローを完成。
- `edu/examples/counterfactual_demo.mlang` & `--counterfactual` オプションで代表シナリオを実行可能。
- グラフ可視化ヘルパー (`graph_to_text/dot`) を公開し、`docs/demo/counterfactual_walkthrough.md` に手順を整理。
- FuzzyJudge/KnowledgeRegistry 向け実データ (`docs/data/fuzzy_samples.json`) を追加し、テスト (`tests/test_fuzzy_real_data.py`) で検証。
- README / Spec / Test Plan / Task Sheet を最新仕様に同期。

## 完了タスク
1. CORE-01: ルール/曖昧判定の本番データ化。
2. CORE-02: カウンターファクトシナリオ整備（DSL + CLI オプション）。
3. CORE-03: 因果グラフ可視化を CLI/Notebook デモへ統合。
4. CORE-04: デモパッケージ（docs/demo/...）。
5. CORE-05: README / Spec / Test Plan 更新。
6. OPS-01: 文書同期ツール整備。

## 現在の状況
- pytest 50件すべて緑。
- CLI は実行結果 + `== Causal Analysis ==` + `== Counterfactual Simulation ==` を表示。
- Notebook では `run_causal_analysis` + `graph_to_text/dot` でグラフを可視化可能。
- 残タスク: OPS-02 (CI で pytest/lint/デモ self-test を常時監視)。

## 次のアクション
1. CI パイプラインに CLI/Notebook デモ実行を組み込み、OPS-02 を完了させる。
2. デモ資料（README/Docs）を外部公開形式へ整備し、Feedback 収集サイクルに備える。
