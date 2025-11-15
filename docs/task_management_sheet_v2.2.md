# MathLang Task Management Sheet v2.2
## Focus: Knowledge-Based Core Completion + Parser Extended Flow

---

| ID | タスク | 内容 | 期限 | 状態 |
|----|---------|------|------|------|
| KB-01 | Normalizer実装 | 加法・乗法の正規化（順序・単位元・定数畳み込み） | Day2 | ☑ |
| KB-02 | KnowledgeRegistry構築 | ルールYAML読込・match関数実装 | Day4 | ☑ |
| KB-03 | 四則ルール定義 | addition/subtraction/multiplication/division 各3件 | Day4 | ☑ |
| KB-04 | Evaluator統合 | normalize → match → result log | Day5 | ☑ |
| KB-05 | Parser再設計実装 | problem/prepare/step/end対応 | Day5 | ☑ |
| KB-06 | エラーハンドリング設計 | 不正構文・曖昧一致・零除算 | Day6 | ☑ |
| KB-07 | テスト整備 | pytest全12ケース整備・CI組込 | Day6 | ☑ |
| KB-08 | ドキュメント同期 | Core DSL / SPECにKB仕様追記 | Day7 | ☑ |
| KB-09 | コアフローテスト追加 | Parser-→Evaluator-→Logger一貫テスト | Day7 | ☑ |
| OPS-01 | 文書同期ツール | make doc-sync / validate rule IDs | Day7 | ☑ |

---

### 廃止／凍結タスク
| ID | 内容 | 理由 |
|----|------|------|
| UI-01 | Notebook UI拡張 | 優先度外・知識ベース完成が先 |
| DEMO-01 | デモパッケージ化 | KB未完成段階では価値なし |
| EXT-01 | 微分・行列拡張 | 四則完成後に再開 |
| DOC-02 | 日本語UIガイド | Phase 2完了後 |

---

### 成功基準
- Evaluatorログに `rule_id` 出力  
- 知識ベースが四則演算を全対応  
- Parserが `problem/prepare/step/end` を正しくAST化  
- pytest 12件成功  → 現在は 35 件の統合テスト（CLI, Evaluator, Fuzzy, Fraction 等）まで拡大し全て緑  
- 仕様書 v2.2 更新反映済  
- CI環境で全テスト緑  
- UIタスク停止・Core完結  

---

### コメント
> 本フェーズの目的は「思考の正当化可能性の確立」。  
> ルールIDを伴う同値検証に加え、曖昧評価（FuzzyJudge）ルートも整備済み。  
> 今後はログ出力の可視化や閾値調整など、学習分析向けの機能強化を検討する。

---

### サマリー
- Python 3.12 / 3.14 で 35 件の pytest がすべて成功。CLI/Evaluator/Fuzzy/Fraction/Polynomial/Symbolic まで含む統合テストを構築済み。
- Core DSL（problem/step/end）や KnowledgeRegistry、FractionEngine の仕様も実装済みで、曖昧評価時の学習ログ出力まで一貫。
- 課題: 仕様書 (MathLang Integrated Spec) がプレースホルダ状態のため、最新アーキテクチャ／テスト状況を反映した正式なドキュメント化が未完。Fuzzy ログを UI/レポートへ見やすく出す導線も次フェーズで要検討。
