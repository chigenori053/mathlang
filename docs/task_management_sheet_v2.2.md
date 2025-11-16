# MathLang Task Management Sheet v2.2
## Focus: Core Architecture Demo Release (Reasoning + Causal)

---

## DSL タスク

### High Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-01 | DSL v2.5 Parser拡張 | `meta/config/mode/prepare/counterfactual` ブロックを AST へマッピングし、旧形式 (`step1:`) と両立 | Day12 | ☑ |
| DSL-02 | DSL v2.5 テスト整備 | `tests/test_parser_v25.py` を拡張し、ステップブロック/prepare/counterfactual を網羅 | Day13 | ☑ |

### Medium Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-03 | DSLドキュメント同期 | `docs/MathLang_Core_DSL_v2.5_Spec.md` と README の DSL 例を最新仕様に合わせる | Day13 | ☑ |
| DSL-04 | DSLサンプル拡充 | `edu/examples/` に v2.5 形式のサンプルを追加し CLI から実行できるようにする | Day13 | ☑ |

### Low Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-05 | DSL LSP/補完調査 | エディタ向けシンタックスハイライト・補完の PoC | Day20 | ☐ |

未完タスク: DSL-05（DSL LSP/補完調査）

---

## Core タスク

### High Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-CLI | Edu/Pro CLI 共通化 | `_run_cli` を中心に Edu/Pro 版を統一、`edu.demo.edu_demo_runner` / `pro.demo_runner` を提供 | Day12 | ☑ |
| CORE-CF | カウンターファクト整備 | CLI `--counterfactual` / API を強化し、Edu/Pro デモから呼び出し可能にする | Day12 | ☑ |

### Medium Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-CI | CI 監視 | `.github/workflows/ci.yml` で pytest + CLI self-test + Notebook smoke を自動化 | Day13 | ☑ |
| CORE-DOC | ドキュメント更新 | README / Spec / Test Plan を Edu/Pro 構成・CLIコマンドへ同期 | Day13 | ☑ |

### Low Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-VIS | 因果グラフ可視化 | `graph_to_text/dot` を Notebook/CLI デモや README に組み込み | Day13 | ☑ |
| CORE-DEMO | デモパッケージ | `docs/demo/` に Edu/Pro 両方のウォークスルーとスクリプトを配置 | Day13 | ☑ |

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
- pytest 53件 + デモシナリオの手動チェックが緑  
- README / Spec / Test Plan がデモ版のワークフローを説明  
- CIでCLI/Notebookデモの self-test を実行（Hello World + causal sample）  

---

### コメント
> Core reasoning + causal のアーキテクチャは完成。  
> ここからは「体験」重視のデモ構築に集中：本番データでの判定精度、介入シナリオのテンプレ化、Notebook/CLIでの可視化を揃える。  
> 53件の自動テスト + デモ手順を公開し、学習ログ→因果分析→カウンターファクトまでをワンストップで確認できる状態を目指す。残タスクは DSL-05 (LSP/補完調査) のみ。

---

### サマリー
- Python 3.12 / 3.14 で 53 件の pytest が成功。CLI/Evaluator/Fuzzy/Fraction/Polynomial/Symbolic/CausalEngine まで網羅。
- CLI ではエラー時に因果サマリを自動表示し、`--counterfactual` 指定でシミュレーション結果も出力。`edu.demo.edu_demo_runner` / `pro.demo_runner` も提供。Notebook では `run_causal_analysis` + `graph_to_text/dot` で可視化可能。
- DSL v2.5 対応は Parser/AST の実装を開始済みで、今後はサンプル・ドキュメント・テストを順次更新予定。
- `docs/test_plan_reasoning.md` でテストシナリオを整理済み。Core タスクは概ね完了し、DSL タスクを優先的に進めるフェーズ。
