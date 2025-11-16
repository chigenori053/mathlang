from core.parser import Parser
from core import ast_nodes as ast


DSL_SOURCE = """
meta:
    id: demo_01
    topic: arithmetic
config:
    fuzzy-threshold: 0.7
    causal: true
mode: causal
problem: (3 + 5) * 4
prepare:
    - x = 5
    - y = x + 2
step:
    before: (3 + 5) * 4
    after: 8 * 4
    note: simplify addition
step:
    before: 8 * 4
    after: 32
end: 32
counterfactual:
    assume:
        x: 10
    expect: 3*x + 2
"""


def test_parser_handles_v25_blocks():
    program = Parser(DSL_SOURCE).parse()
    assert isinstance(program, ast.ProgramNode)
    meta = next(node for node in program.body if isinstance(node, ast.MetaNode))
    assert meta.data["id"] == "demo_01"
    config = next(node for node in program.body if isinstance(node, ast.ConfigNode))
    assert config.options["causal"] is True
    mode = next(node for node in program.body if isinstance(node, ast.ModeNode))
    assert mode.mode == "causal"
    prepare = next(node for node in program.body if isinstance(node, ast.PrepareNode))
    assert prepare.statements == ["x = 5", "y = x + 2"]
    steps = [node for node in program.body if isinstance(node, ast.StepNode)]
    assert len(steps) == 2
    assert steps[0].before_expr == "(3 + 5) * 4"
    assert steps[0].note == "simplify addition"
    cf = next(node for node in program.body if isinstance(node, ast.CounterfactualNode))
    assert cf.assume["x"] == "10"
    assert cf.expect == "3*x + 2"
