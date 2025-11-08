# MathLang 開発タスク管理シート

## レジェンド
- **フェーズ**: README/仕様書で定義されたPhase 1〜4に対応。
- **優先度**: H (高) / M (中) / L (低)。
- **状態**: Backlog（未着手）/ In Progress（着手中）/ Blocked（阻害要因あり）/ Review / Done。

## サマリー（2025-11-08 時点）
- Phase 1（P1-02〜P1-06）は6/6完了。DSL/CLI/Examples/失敗系テストまでデモ基盤は整備済み。
- Phase 2は`SymbolicEngine`本体＋Evaluator統合＋AST最適化＋CLI `--symbolic-trace`実装まで完了し進捗80%。残タスクはSymPy/Jupyter環境整備と教材整備（P2-04, P2-05）。
- 多項式四則演習のサンプル／ドキュメントは着手前だが、Evaluator側のシンボリック説明機構が整備されたことでP2-05の準備が整った。
- Demo版完成までの流れは「Hello World確認 → 多項式四則機能 → 演習Notebook → Demoパッケージ」の4段ステップで約6週間を想定。

## 進行評価
| フェーズ/領域 | 進捗率 | 状況・メモ |
|---------------|--------|-------------|
| Phase 1（DSL/CLI/Tests） | 100% | 仕様で定義されたP1タスクは全てDone。CLI/Examplesも稼働確認済み。 |
| Phase 2（SymbolicAI） | 80% | `SymbolicEngine`本体＋Evaluator統合＋AST最適化＋CLI `--symbolic-trace`実装済。環境整備と教材作成が残件。 |
| Phase 3（UI/Logs/Demo） | 10% | docs/READMEにCLI更新を反映済み。Notebookや学習ログAPIは未着手。 |
| Phase 4（リリース準備） | 0% | タスク定義のみ。デモ完成後に着手。 |

## タスク一覧
| ID | フェーズ | カテゴリ | タスク概要 | 完了条件 | 担当 | 優先度 | 状態 | 期限 | 備考/依存 |
|----|----------|----------|------------|----------|------|--------|-------|------|------------|

| P1-02 | Phase 1 | AST | ASTノード定義の整理 | `core/ast_nodes.py`に主要statement/expressionノードを網羅 | TBD | M | Done | 2025-11-05 | 2025-11-08レビュー済 |
| P1-03 | Phase 1 | Evaluator | ステップ実行とログ出力 | `core/evaluator.py`が実行順ログを生成、簡単なサンプルで再現性保証 | TBD | H | Done | 2025-11-10 | ステップ実行trace確認済 |
| P1-04 | Phase 1 | テスト | Parser/Evaluator向けpytest整備 | `tests/test_parser.py`と`tests/test_evaluator.py`が主要ケースを網羅しCI緑 | TBD | H | Done | 2025-11-12 | pytest 21ケース成功（2025-11-08時点）。詳細はdocs/test/Report.md参照 |
| P1-05 | Phase 1 | CLI/UX | CLIとExamples整備 | `main.py`でファイル実行でき、`examples/`配下にチュートリアルが存在 | TBD | M | Done | 2025-11-15 | README/仕様書/チェックリストを更新済み |
| P1-06 | Phase 1 | テスト | エラーパスと境界値テスト | division-by-zero/未定義変数/多重unary等の失敗系がpytestで再現 | TBD | M | Done | 2025-11-18 | tests/test_evaluator.pyでカバー |
| P2-01 | Phase 2 | SymbolicAI | SymPy連携PoC | `core/symbolic_engine.py`で`simplify`/`explain`最小実装、2例以上のテスト付き | TBD | H | Done | 2025-12-03 | PoCコード＋`tests/test_symbolic_engine.py`/`tests/test_cli.py`で最小機能確認済 |
| P2-02 | Phase 2 | AST最適化 | AST最適化パス追加 | 冗長演算を統合する最適化が1ケース以上で効果検証 | TBD | M | Done | 2025-12-08 | `core/optimizer.py`新設＋`tests/test_optimizer.py`整備で定数畳み込み/代入展開を確認（2025-11-08） |
| P2-03 | Phase 2 | SymbolicAI | Evaluator統合＆trace拡張 | Evaluator/CLIからSymbolicEngineを呼び出し、`show`出力で簡約結果を提示 | TBD | H | Done | 2025-12-05 | `Evaluator(symbolic_engine_factory)`導入、CLI `--symbolic-trace`で統合。テスト追加済（2025-11-08） |
| P2-04 | Phase 2 | インフラ | SymPy/Jupyter環境整備 | SymPyをCI/開発環境でインストールし、`python main.py --symbolic`が実機で成功 | TBD | H | In Progress | 2025-11-25 | README/Specへ手順追記済。uvテスト環境での実行に成功。CI/devcontainer更新が残課題。 |
| P2-05 | Phase 2 | SymbolicAI | 多項式四則演習スクリプト | 多項式の加減乗除を扱うMathLangサンプルとpytestを追加し、CLI/`--symbolic`で説明可能 | TBD | H | Backlog | 2025-12-02 | Evaluator統合により準備完了。教材・テスト実装が次タスク。 |
| P3-01 | Phase 3 | UI | JupyterLabデモノートブック | `examples/`配下にデモNotebookと手順書を配置 | TBD | M | Backlog | 2025-12-20 | P1/P2成果に依存 |
| P3-02 | Phase 3 | 学習ログ | 学習ログ導出API | 評価過程をJSONログに保存する`Evaluator`拡張 | TBD | L | Backlog | 2025-12-22 | P3-01と調整 |
| P3-03 | Phase 3 | Demo | Demoパッケージ化 | Notebook/CLI/シンボリック例をまとめた`demo/`配布物と実行スクリプトを整備 | TBD | H | Backlog | 2025-12-27 | P3-01/02とRelease checklist入力が前提 |
| P4-01 | Phase 4 | リリース | Beta v0.9リリース準備 | リリースノート+タグ付け+README更新 | TBD | M | Backlog | 2026-01-15 | 全タスク完了前提 |
| OPS-01 | Cross | ドキュメント | README/仕様書の二重管理整備 | 仕様更新時の差分手順テンプレ作成 | TBD | M | Backlog | 2024-11-15 | Agent.md参照 |

## デモ版完成までのプロセス（案）
| ステップ | 期間目安 | 主担当タスク | 成果物/Exit Criteria | リスク・備考 |
|---------|-----------|---------------|----------------------|---------------|
| 1. Hello World実行保証 | 〜11/18 | P1-05, P2-04 | `python main.py -c "show 'Hello World'"`などで確実に表示でき、README/Specに手順記載 | SymPy未導入の環境差異によりCLIが再現できない可能性 |
| 2. 多項式四則メカニズム | 11/19〜12/02 | P2-01, P2-03, P2-05 | SymPy導入済みで、Evaluator/CLIが多項式の加減乗除・追跡説明を表示（四則演習スクリプト含む） | SymPy APIとの整合、数値/象徴混在の誤差 |
| 3. 演習Notebook整備 | 12/03〜12/15 | P3-01, P3-02 | 「Hello World紹介＋多項式四則演習」のJupyter Notebookと学習ログ出力 | Notebookメンテ負荷、UI要件の追加発生 |
| 4. Demoパッケージ化 | 12/16〜12/27 | P3-03, OPS-01, P4-01 | `demo/`配布物、CLI/Notebook手順書、Release checklist更新、デモ発表用ビルド | ドキュメント差異や依存ライブラリバージョンずれ |

## デモ到達度チェック（Hello World & 多項式演習）
| 項目 | ステータス | 根拠/課題 |
|------|------------|------------|
| Hello World 表示 | Done | `python main.py -c "show 'Hello World'"`で動作確認済。README/Specにも手順記載済み。 |
| 多項式 四則演習 | In Progress | DSL/Parserは四則対応済だが、演習サンプル・Symbolic説明・自動テストが未整備（P2-05）。 |
| 演習 Notebook | Backlog | 未着手。P3-01/02でHello World＋多項式演習の教材化とログ出力が必要。 |

## 追加メモ
- タスク追加時はIDをフェーズ別に連番で拡張（例: P2-03）。
- 依存関係が変わった場合は備考欄を更新し、必要に応じてAgent.mdに同期メモを記載。
- ステータス更新はPRレビュー時・スプリント開始時など定期イベントで行う。
