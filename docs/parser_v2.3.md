# Parser Specification v2.3
## MathLang DSL Parser – problem/prepare/step/end

### 1. DSL Grammar

```
problem <identifier>
    prepare:
        <assignment>*
    step:
        <equation>
    step:
        <equation>
    ...
end
```

### 2. AST Nodes

```python
@dataclass
class ProblemNode:
    name: str
    prepare: PrepareNode
    steps: List[StepNode]

@dataclass
class PrepareNode:
    assignments: List[AssignmentNode]

@dataclass
class AssignmentNode:
    name: str
    value: ExpressionNode

@dataclass
class StepNode:
    before: ExpressionNode
    after: ExpressionNode
```

### 3. RationalNode Rules (Parser v2.3)

- `<expr>/<expr>` を **RationalNode** として構文解析する  
- 例:
  ```
  1/2 → RationalNode(Const(1), Const(2))
  a/b → RationalNode(Symbol(a), Symbol(b))
  ```

### 4. Validation Rules

- `problem` ～ `end` が 1 回ずつ必要  
- `step:` は 1 回以上必須  
- `prepare:` は省略可  
- 行解析時、構文違反は `InvalidSyntaxError`
