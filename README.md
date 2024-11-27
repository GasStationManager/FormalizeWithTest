# FormalizeWithTest

Main Essay: [A Proposal for Safe and Hallucination-free Coding AI](https://gasstationmanager.github.io/ai/2024/11/04/a-proposal.html)

This repository concerns autoformalization of coding problems,
i.e. translation from coding tasks in natural language into formal specifications in Lean,
for the purpose of generating training data for coding AIs.

It contains exploration of ideas from Section 3, Project 3 of the essay.
In particular, automated verification of translated specifications using the test cases from the origional problem.

# Installation

1. Install Poetry
2. Install Lean 4
3. Clone the repository
4. Clone LeanTool
5. Install Mathlib

# Files

- `load_data.py`: loads from the `hackercupai/hackercup` data set from HuggingFace.
  Alternatively, can use the [code_contests](https://huggingface.co/datasets/deepmind/code_contests) data set. Writes output in a JSONL file. 
- `translate.py`: calls an LLM to translate each problem statement into formal specification in Lean, and test cases into Lean data that can be plugged in.
  Uses LiteLLM, which allows you to plug in different LLMs; from commercial APIs including OpenAI and Anthropic, to open source models which you can serve via vLLM or ollama.
- `verify.py`: tries to verify each translated formal specification by plugging in test cases, and proving/disproving each of the resulting propositions. 
  Currently the proof procedure just calls a predefined combination of automated tactics like simp, decide, omega and rfl.

# TODO

- Check for syntax errors before attempting proof, by plugging in `sorry`s, for the theorem statement,
and then after plugging in test cases.
- plug in theorem proving LLMs, including DeepSeek Prover 1.5
