# MathLang CLI UI Specification (edu / pro / demo)
Version: 0.1
Status: Draft
Target: Codex / MathLang Dev Environment

## 1. Purpose
This document defines the CLI directory layout and execution rules for MathLang's edu, pro, and demo environments. It ensures that each variant can be executed and tested using CLI-based workflows compatible with Codex.

## 2. Directory Structure
mathlang/
 ├── core/
 ├── edu/
 │    ├── cli/
 │    │     ├── main.py
 │    │     ├── commands.py
 │    │     └── scenarios/
 │    ├── ui/
 │    ├── notebooks/
 │    └── ...
 ├── pro/
 │    ├── cli/
 │    │     ├── main.py
 │    │     ├── commands.py
 │    │     └── scenarios/
 │    ├── tools/
 │    ├── notebooks/
 │    └── ...
 ├── demo/
 │    ├── demo_cli.py
 │    ├── demo_config.yaml
 │    └── scenarios/
 └── tests/

## 3. CLI Execution Formats
Edu:
  python -m edu.cli.main --scenario <scenario>

Pro:
  python -m pro.cli.main --mode <mode> --scenario <scenario>

Demo:
  python -m demo.demo_cli --scenario <scenario>

## 4. Output Format
Each CLI must print step-by-step logs including:
- Before/After
- Rule ID
- Fuzzy Score
- Causal Explanation

## 5. Testing Requirements
- pytest must include:
  - test_edu_cli.py
  - test_pro_cli.py
  - test_demo_cli.py

## 6. CI Integration
CI must run:
  python -m edu.cli.main --scenario arithmetic
  python -m pro.cli.main --mode causal --scenario basic
  python -m demo.demo_cli --scenario minimal
