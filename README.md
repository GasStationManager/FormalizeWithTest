# FormalizeWithTest: Automated Verification for Autoformalization of Coding Problems

Main Essay: [A Proposal for Safe and Hallucination-free Coding AI](https://gasstationmanager.github.io/ai/2024/11/04/a-proposal.html)

This repository concerns autoformalization of coding problems,
i.e. translation from coding tasks in natural language into formal specifications in Lean,
for the purpose of generating training data for coding AIs.
It contains exploration of ideas from Section 3, Project 3 of the essay.

Here is a summary of our approach. 
A major challenge of autoformalization efforts is the evaluation of the quality of the translations in a scalable manner. 

For coding problems, the situation may be better, especially if the dataset comes with test cases for each problem. In short, we can repurpose these test cases to serve as checks on the fidelity of the translations.
If the translation is faithful, the formal specification and the test cases should be compatible, and this check can be automated.

For example, consider the following coding task: write a function that takes two integers and returns their sum. 
The test cases consists of input-output pairs, e.g. "2 3 5" for 2+3=5. Prompt the formalizer LLM so that its output is of the following format.
```
def add (a b:Int) : Int := sorry
def add_prop (a b out: Int) := a+b=out
theorem add_spec (a b:Int): add_prop a b (add a b) :=sorry
```

Then plug the test cases into add_prop, and try to prove
```
theorem prop_true: add_prop 2 3 5
```
or its negation
```
theorem prop_false: Not (add_prop 2 3 5)
```

Observe that:
1. We do not need to implement the function `add` or the theorem `add_spec`. 
2. `prop_true` and `prop_false` are often simple to prove; automated theorem proving methods can be effective.
3. If all test cases pass, we have high confidence that the formal specification (theorem add_spec) is a faithful representation of the problem description. If one of the test cases fail, we know that the formal specification and the problem description differ.

This can be used as a filter in a autoformalization pipeline. Furthermore, the pass/fail results can be used as ground truth to train better translation models.

This repository is a proof of concept. In practice, you may want to plug in your own datasets, your own formalizer LLM,
and a custom set of provers.

# Preliminary Results
- Dataset: `code_contests_sample_train_short.jsonl`, a random selection of 30 problems from the 
 [code_contests](https://huggingface.co/datasets/deepmind/code_contests) data set.
I focused on relatively simple problems: I restricted the selection to problems with codeforces rating (`cf_rating` field) in the range (0,1100].
- Formalization: a simple pipeline where I prompted an LLM (Claude Sonnet 3.5) to translate problem descriptions into
formal specification in Lean 4. Checks code with Lean and feed any syntax errors to back to the LLM to fix.
Results in a set of 17 formal specifications that did not contain syntax errors. 
- Verification: the proof procedure is a predefined combination of automated tactics like simp, decide, omega, rfl, and aesop.
10 of the formal specifications passed the tests. 1 failed (proven to be false). The remaining
ones (6) were unproven (3 of these had some but not all test cases proven true).



# Installation

1. Install Poetry
2. Install Lean 4
3. Clone the repository; cd into the directory
4. Clone [LeanTool](https://github.com/GasStationManager/LeanTool)
5. Install Mathlib

# Files

- `load_data.py`: loads from the `hackercupai/hackercup` data set from HuggingFace. Loads data from a specific year (default 2023).
Writes output in a JSONL file. Usage: `poetry run python load_data.py output.jsonl 2023`
-  Alternatively, can use the [code_contests](https://huggingface.co/datasets/deepmind/code_contests) data set. 
The file `code_contests_sample_train_short.jsonl` is a random selection of 30 problems from the data set, restricted
to problems with `cf_rating` in the range of (0,1100]. 
- `translate.py`: calls an LLM to translate each problem statement into formal specification in Lean, and test cases into Lean data that can be plugged in.
  Uses LiteLLM, which allows you to plug in different LLMs; from commercial APIs including OpenAI and Anthropic, to open source models which you can serve via vLLM or ollama.
Uses the utility [LeanTool](https://github.com/GasStationManager/LeanTool) to run the code with Lean to check for syntax errors, and provide feedback to the LLM so that it can attempt to fix the errors.
- `verify.py`: tries to verify each translated formal specification by plugging in test cases, and proving/disproving each of the resulting propositions. 
  Currently the proof procedure calls a predefined combination of automated tactics like simp, decide, omega, rfl, and aesop.
Also a SMT solver from the lean-smt library.
Optionally, calls an LLM to prove the test cases. 


