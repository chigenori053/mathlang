# Counterfactual & Causal Analysis Walkthrough

1. `python main.py --file examples/counterfactual_demo.mlang`  
   - 実行後 `== Causal Analysis ==` セクションで原因ステップと修正候補を確認。

2. `python main.py --file examples/counterfactual_demo.mlang --counterfactual '{"phase": "step", "index": 2, "expression": "8 * 4"}'`  
   - `== Counterfactual Simulation ==` で置換結果・新しい end 表現を確認。

3. Notebook では以下を実行  
```python
from core.causal.integration import run_causal_analysis
from core.causal.graph_utils import graph_to_text
records = logger.to_list()
engine, report = run_causal_analysis(records, include_graph=True)
print(graph_to_text(report["graph"]))
```

4. `docs/data/fuzzy_samples.json` を用いて FuzzyJudge の実データ評価を再現 (`tests/test_fuzzy_real_data.py` を参照)。
