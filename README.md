# FormalizeWithTest

Main Essay: [A Proposal for Safe and Hallucination-free Coding AI](https://gasstationmanager.github.io/ai/2024/11/04/a-proposal.html)

This repository concerns autoformalization of coding problems,
i.e. translation from coding tasks in natural language into formal specifications in Lean.
It contains exploration of ideas from Section 3, Project 3 of the essay.

In particular, automated verification of translated specifications using the test cases from the origional problem.

# Files
- `load_data.py`: loads from the `hackercupai/hackercup` data set from HuggingFace.
  Alternatively, can use the [code_contests](https://huggingface.co/datasets/deepmind/code_contests) data set. Writes output in a JSONL file. 
- `translate.py`: translate each problem statement into formal specification in Lean, and test cases into Lean data that can be plugged in.
- `verify.py`: tries to verify each translated formal specification by plugging in test cases, and proving/disproving each of the resulting propositions. 
