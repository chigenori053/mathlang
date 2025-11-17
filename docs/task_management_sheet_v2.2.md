# MathLang Task Management Sheet v2.2
## フォーカス: Edu/Pro UI/CLI 仕様順守と Evaluator v2 展開

---

## DSL タスク

### High Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-06 | DSL v2.5 ブロック完全対応 | `MathLang_Core_DSL_v2.5_Spec.md` 第4〜5章で定義されている `meta/config/mode/prepare/counterfactual` ブロックを Parser→AST→Evaluator まで一貫したフローで処理し、旧来の `step1:` 形式とも両立させる | Day15 | 未着手 |
| DSL-07 | DSL v2.5 サンプル＆シナリオ刷新 | `edu/examples/` / `pro/examples/` / `docs/demo/*.md` 内のサンプルを v2.5 構文に差し替え、`prepare` や `counterfactual`、`note` を含む代表ケースを CLI/Notebook から実行できるようにする | Day16 | 未着手 |

### Medium Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-08 | DSL ドキュメント同期 | README / `docs/MathLang_Core_DSL_v2.5_Spec.md` / `edu/README.md` に掲載された例示コード・構文チャート・FAQ を横並びで更新し、参照先による仕様差分を解消する | Day17 | 未着手 |
| DSL-09 | DSL schema テスト強化 | `tests/test_parser_v25.py` に `meta`・`config`・`prepare`・`counterfactual` の組み合わせパターンを追加し、AST スナップショットを導入してリグレッション検知を強化する | Day17 | 未着手 |

### Low Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| DSL-10 | DSL LSP/補完計画 v2 | v2.5 で増加した DSL セクションを対象に、補完/LSP 対応 PoC の要求事項とエディタ別の優先順位を整理した計画書を作成する | Day20 | 未着手 |

未完タスク: DSL-06, DSL-07, DSL-08, DSL-09, DSL-10

---

## Core タスク

### High Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-01 | Evaluator v2 状態機械 | `docs/Evaluator_v2_Specification.md` に定義された ok/mistake/fatal ログ仕様と `run()` の挙動を `core/evaluator.py` に反映し、新ステートマシンで fatal 発生時に停止・bool を返すよう実装する | Day15 | ✅ 完了 |
| CORE-02 | LearningLogger v2 | `core/learning_logger.py` を Spec 5.1 の形式（`step_index` / `phase` / `status` / `rule_id` / timestamp）へ再設計し、Evaluator・CLI・Notebook からの呼び出しコードをすべて更新する | Day15 | ✅ 完了 |
| CORE-03 | CausalEngine/CF 仕上げ | `core/causal/*.py` を Causal Spec v1（node/edge/why_error/counterfactual_result）と一致させ、`tests/test_causal_engine.py` / `tests/test_causal_integrations.py` が最新ログ構造で成功するよう整備する | Day16 | ✅ 完了 |
| CORE-04 | Config/Mode 反映 | DSL の `config:` / `mode:` 情報を Evaluator・Fuzzy・Causal・Polynomial 各モードに反映させ、CLI/Notebook から `strict` / `fuzzy` / `causal` / `cf` を切り替えられるようにする | Day16 | ✅ 完了 |

### Medium Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-05 | Polynomial/Fuzzy 同期 | `core/polynomial_evaluator.py` と FuzzyJudge 連携を v2 ログ構造へ揃え、`tests/test_polynomial_evaluator.py` を含む関連テストを更新してリグレッションを防ぐ | Day17 | ✅ 完了 |
| CORE-06 | KnowledgeRegistry メタ情報拡張 | ルール記述やカテゴリを CausalEngine に渡すため `core/knowledge_registry.py` を拡張し、`run_causal_analysis` の `rule_details` 出力を保証する | Day17 | ✅ 完了 |

### Low Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| CORE-07 | グラフ可視化パイプライン | `graph_to_text/dot` を Notebook/CLI から利用するパイプラインを整備し、Causal Spec 6章の可視化要件を満たす | Day18 | 未着手 |
| CORE-08 | Counterfactual シナリオ集 | `docs/demo/` および `edu/pro/examples/` に再利用可能な介入テンプレートを整備し、CLI の `--counterfactual` から選択・実行できるようにする | Day19 | 未着手 |

未完タスク: CORE-07, CORE-08

---

## UI/CLI タスク

### High Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| UICLI-01 | edu/ ディレクトリ再編 | `docs/MathLang UI Directory Specification.md` 第3章に沿って `edu/ui/` `edu/notebooks/` `edu/lessons/` `edu/demo/` を整備し、ランナー・設定ファイル・README を配置する | Day15 | ✅ 完了 |
| UICLI-02 | pro/ ディレクトリ再編 | 同仕様書第4章どおりに `pro/api/` `pro/tools/` `pro/notebooks/` `pro/demo/` `pro/config/` を揃え、研究向けサンプルと README を用意する | Day15 | ✅ 完了 |
| UICLI-03 | CLI 3 系統実装 | `docs/MathLang_CLI_UI_Spec.md` の構成に従い `edu/cli/main.py`、`pro/cli/main.py`、`demo/demo_cli.py`＋`scenarios/` を実装し、共通 `_run_cli` をモジュール化する | Day16 | ✅ 完了 |
| UICLI-04 | CLI self-test & CI | `tests/test_edu_cli.py` / `tests/test_pro_cli.py` / `tests/test_demo_cli.py` を追加し、GitHub Actions で Spec 第6章に記載された 3 コマンドを実行する CI を構築する | Day16 | ✅ 完了 |

### Medium Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| UICLI-05 | Notebook テンプレ整備 | `edu/notebooks/edu_intro.ipynb` など教育向け 2 本、`pro/notebooks/pro_intro_causal.ipynb` など研究向け 2 本の計 4 本を作成し、Core API と UI ヘルパーの使い方を解説する | Day18 | 未着手 |
| UICLI-06 | Demo ドキュメント刷新 | `docs/demo/*.md` を新 CLI／ディレクトリ構成に合わせて更新し、スクリーンショットとログ例を差し替える | Day18 | 未着手 |

### Low Priority
| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| UICLI-07 | UI テーマ設定反映 | `edu/config/edu_ui_settings.yaml` と `pro/config/pro_settings.yaml` のテーマ情報を UI レイヤーで読み込み、Notebook/CLI から切り替え可能にする | Day20 | 未着手 |
| UICLI-08 | シナリオ作成ツール | `edu/lessons/` や `pro/examples/` を自動生成できる簡易スクリプト／テンプレ CLI を `tools/` に追加する | Day21 | 未着手 |

未完タスク: UICLI-05, UICLI-06, UICLI-07, UICLI-08

---

### 廃止／凍結タスク
| ID | 内容 | 理由 |
|----|------|------|
| EXT-01 | 微分・行列拡張 | デモ版スコープ外 |
| DOC-02 | 日本語 UI ガイド | Core デモ完成後に再開 |

---

### 成功基準
- `edu/` と `pro/` のディレクトリが UI Spec v0.1 の必須ファイルを満たし、README と Notebook から動作確認できる  
- CLI (`python -m edu.cli.main --scenario`, `python -m pro.cli.main --mode causal`, `python -m demo.demo_cli`) が Spec 第3〜4章通りの出力形式で動作し、CI で自動検証される  
- Evaluator v2 / LearningLogger v2 / CausalEngine v1 が Spec に定義されたログ形式（ok/mistake/fatal + step_index + rule_id）を共有し、counterfactual 実行も CLI オプションから呼び出せる  
- `tests/test_parser_v25.py`、`tests/test_causal_*`、`tests/test_edu_cli.py` など 53 件超の pytest がすべて成功する  
- `docs/demo/*` および README 群が最新ワークフロー（DSL v2.5 → CLI/Notebook → causal/counterfactual）を説明する

---

### コメント
> UI/CLI 再編と Evaluator v2／Logger／Causal の大規模改修が同時進行になるため、まずディレクトリ構造とランナーの骨格を固め、その後ログ仕様の互換テストを整備する。DSL v2.5 のサンプル刷新と Notebook／lesson 群の整備は CLI 仕様固めと並行して進める。CI では CLI 3 系統と主要 pytest を常時実行し、構造変更によるリグレッションを即座に検知する体制を敷く。

---

### サマリー
- MathLang Core は DSL v2.5／Causal Engine／CLI 仕様群（Integrated Spec、UI Directory Spec、CLI UI Spec、Evaluator v2 Spec、Causal Spec v1）に沿った大規模アップデートに着手する段階であり、既存コードは旧構成（単一 CLI・Logger v1）のままなので、新仕様への移行タスクを優先度別に整理した。  
- DSL 面では Parser に必要な部品が揃っている一方で、AST→Evaluator→サンプルの一貫性やドキュメント同期が未着手であるため、DSL-06〜09 で仕様適合とテスト拡充を実施する。  
- Core では Evaluator v2 と LearningLogger v2 が未実装で、CausalEngine/Counterfactual も Spec v1 と差分が残っているため、CORE-01〜04 を最優先で進め、Polynomial/Fuzzy/KnowledgeRegistry への波及は CORE-05/06 で吸収する。  
- UI/CLI では edu/pro/demos のディレクトリ再編や CLI 3 系統、CI テストが未整備のため、UICLI-01〜04 を Day15-16 で完了させ、その後 Notebook・ドキュメント・テーマ連携（UICLI-05〜08）に派生させる計画。
