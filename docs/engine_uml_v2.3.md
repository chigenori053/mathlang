# Engine UML Design v2.3
## ArithmeticEngine / FractionEngine / Evaluator / Registry

---

```mermaid
classDiagram

class Evaluator {
    +evaluate_problem(problem)
    +choose_engine(ast)
}

class ArithmeticEngine {
    +normalize(ast)
    +check_equivalence(before, after)
}

class FractionEngine {
    +normalize(ast)
    +check_equivalence(before, after)
}

class KnowledgeRegistry {
    +match(before, after, domain)
}

class RationalNode {
    numerator
    denominator
}

Evaluator --> ArithmeticEngine : uses
Evaluator --> FractionEngine : uses
Evaluator --> KnowledgeRegistry : queries
FractionEngine --> RationalNode
ArithmeticEngine --> ExpressionNode
KnowledgeRegistry --> RuleHit
```

---

## 設計ポイント

- Evaluator は AST 内に RationalNode を検出すると FractionEngine を使用  
- ArithmeticEngine と FractionEngine はどちらも  
  `normalize()` → `match()` → `EvaluationResult` を返す  
- KnowledgeRegistry が ARITH-* と FRAC-* を domain で振り分ける  
