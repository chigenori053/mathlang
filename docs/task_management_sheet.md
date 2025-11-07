# MathLang 開発タスク管理シート

## レジェンド
- **フェーズ**: README/仕様書で定義されたPhase 1〜4に対応。
- **優先度**: H (高) / M (中) / L (低)。
- **状態**: Backlog（未着手）/ In Progress（着手中）/ Blocked（阻害要因あり）/ Review / Done。

## サマリー（2025-11-07 時点）
- Phase 1 がクリティカルパス。Parser（基本文法）実装済、Evaluator結合テストは未着手。
- SymbolicEngineはPoC段階のままなので、SymPy連携プロトタイプを優先度Hで追加。
- UIタスクはPhase 3開始まではBacklogに留め、仕様固めを優先。

## タスク一覧
| ID | フェーズ | カテゴリ | タスク概要 | 完了条件 | 担当 | 優先度 | 状態 | 期限 | 備考/依存 |
|----|----------|----------|------------|----------|------|--------|-------|------|------------|

| P1-02 | Phase 1 | AST | ASTノード定義の整理 | `core/ast_nodes.py`に主要statement/expressionノードを網羅 | TBD | M | Backlog | 2025-11-05 | P1-01完了後レビュー |
| P1-03 | Phase 1 | Evaluator | ステップ実行とログ出力 | `core/evaluator.py`が実行順ログを生成、簡単なサンプルで再現性保証 | TBD | H | Backlog | 2025-11-10 | P1-01/02依存 |
| P1-04 | Phase 1 | テスト | Parser/Evaluator向けpytest整備 | `tests/test_parser.py`と`tests/test_evaluator.py`が主要ケースを網羅しCI緑 | TBD | H | Backlog | 2025-11-12 | P1-01〜P1-03出力を参照 |
| P2-01 | Phase 2 | SymbolicAI | SymPy連携PoC | `core/symbolic_engine.py`で`simplify`/`explain`最小実装、2例以上のテスト付き | TBD | H | Backlog | 2025-12-03 | P1系完了が前提 |
| P2-02 | Phase 2 | AST最適化 | AST最適化パス追加 | 冗長演算を統合する最適化が1ケース以上で効果検証 | TBD | M | Backlog | 2025-12-08 | P2-01から独立可 |
| P3-01 | Phase 3 | UI | JupyterLabデモノートブック | `examples/`配下にデモNotebookと手順書を配置 | TBD | M | Backlog | 2025-12-20 | P1/P2成果に依存 |
| P3-02 | Phase 3 | 学習ログ | 学習ログ導出API | 評価過程をJSONログに保存する`Evaluator`拡張 | TBD | L | Backlog | 2025-12-22 | P3-01と調整 |
| P4-01 | Phase 4 | リリース | Beta v0.9リリース準備 | リリースノート+タグ付け+README更新 | TBD | M | Backlog | 2026-01-15 | 全タスク完了前提 |
| OPS-01 | Cross | ドキュメント | README/仕様書の二重管理整備 | 仕様更新時の差分手順テンプレ作成 | TBD | M | Backlog | 2024-11-15 | Agent.md参照 |

## 追加メモ
- タスク追加時はIDをフェーズ別に連番で拡張（例: P2-03）。
- 依存関係が変わった場合は備考欄を更新し、必要に応じてAgent.mdに同期メモを記載。
- ステータス更新はPRレビュー時・スプリント開始時など定期イベントで行う。
