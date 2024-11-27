import asyncio
#from litellm import completion
import sys
import jsonlines
import json
import time
import traceback
from LeanTool.leantool import interactive_lean_check,check_lean_code

model_choice='sonnet'

models={
  'sonnet':'anthropic/claude-3-5-sonnet-20241022',
  'qwen':'ollama/hf.co/bartowski/Qwen2.5-Coder-14B-Instruct-GGUF:IQ4_XS',
  'deepseek':'ollama/hf.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF:Q5_K_M',
  'o1-mini':'o1-mini',
  'o1-preview':'o1-preview',
  'gpt':'gpt-4o'
}

content_template="""
You are given a JSON object describing a coding problem.
The "description" field contains the problem description. The {test_field} field contains test cases.
Your task is to translate it into the following in the language 
lean 4: a function signature of the function to be implemented, and 
a formal specification of the requirement the function must satisfy. Again, your task is not to solve the problem,
but to give a complete formal specification of the requirements.

The formal specification should further consist of 
1. a definition of a property (a function returning a Prop) that takes in the input and output values, and specify that the output value is a correct solution of the problem given the inputs. It should not call the function. 
2. the theorem statement which references the property and the function, and states that for all input values, the output value produced by the function satisfy the above property.
Furthermore, reformat the test cases in the {test_field} field in the input JSON to be a list of strings that 
can be plugged into the property definition. 
Do not try to implement the function or to prove the theorem.

For example, for the task of adding two natural numbers, the function signature would be: 
def add (a b:Nat):Nat 
And the theorem statement would be: 
def add_prop (a b out:Nat):= a+b=out 
theorem add_spec (a b:Nat): add_prop a b (add a b)
And the test cases should be in the format "1 1 2"
Make sure that each test case can be plugged into the property, e.g. add_prop 1 1 2 should be valid Lean 4 code that evaluates to a Prop.
Omit test cases that involve very large numbers (> 1000), or large amount of input data. Each problem should containt at least one test case.

Again, in the body of the property definition do not call the function.
The body of the property definition should be complete: no 'sorry's, and if you need to make helper
functions, do so and do not put 'sorry' in their bodies.
If you need to use arr[i] to access element of array or list at index i, and you have not yet established
that i is a valid index, you may use arr[i]? notation to return an Option value, 
or arr[i]! notation to leave the proof obligation to the future prover.

Before producing the final output, use the provided tool to verify your lean code is valid.
Put ":=sorry" after the function signature and theorem signature before sending the code to the tool.
Also include the test cases as definitions, e.g. "def test_1 := add_prop 1 1 2"
Analyze the tool's output, if it indicates an error, identify the reason the error occurs and modify your
code. Use the tool again until there are no errors (warnings due to the sorry in the function and theorem are fine). You may call the tool at most 5 times for this task.

Format your final output as a JSON Object.

You are encouraged to reason step by step; put your thoughts in the <Thinking> ... </Thinking> tag,
then put the final (JSON) output in the <Result> ... </Result> tag. For example:

<Result>
{{
  "function_signature": "def add (a b:Nat):Nat",
  "property_name": "add_prop",
  "property_def": "def add_prop (a b out:Nat):= a+b=out",
  "theorem_signature": "theorem add_spec (a b:Nat): add_prop a b (add a b)",
  "tests": ["1 1 2", "1 2 3"]
}}
</Result>

Any helper function definitions goes in "property_def".

If your Lean 4 code contains newline characters, please properly escape them when converting to json.
Similarly, if your test cases contain string data, escape the data into proper json.

START OF INPUT
{input_json}
END OF INPUT

START OF OUTPUT
"""



def extract_quote (output, start_str='```json',end_str='```'):
        if start_str in output:
            res=output.split(start_str)[1].split(end_str)[0]
            return res
        else:
            return output

def verify_output(output:dict):
    code=f"""
import Mathlib
{output['function_signature']}
:=sorry

{output['property_def']}
{output['theorem_signature']}
:=sorry
"""
    if 'tests' not in output or len(output['tests'])==0: 
        return {'success':False, 'error':'No test cases'}

    for i,tc in enumerate(output['tests']):
        code+=f"def test_{i}:={output['property_name']} {tc}\n"
    return check_lean_code(code)

async def translate(inp_json, test_field='"input" and "output"'):
  msg= content_template.format(input_json=inp_json, test_field=test_field)
  res=await interactive_lean_check(msg, model=models[model_choice])
  if 'final_code' in res:
    ret=res['final_code']
    ret=extract_quote(ret)
    #print (ret)
    ret= json.loads(ret)
    chk=verify_output(ret)
    if chk['success']:
        return ret
    else:
        print (chk)
        return None
  else:
    print (res)
    return None



async def main():
  with jsonlines.open(sys.argv[1]) as f:
    with jsonlines.open(sys.argv[2], mode='w') as fout:
      if len(sys.argv)>3:
        kwa={'test_field':sys.argv[3]}
      else:
        kwa={}
      for jo in f:
        time.sleep(1)
        if 'test_field' in kwa:
          inp_jo={kwa['test_field']: jo[kwa['test_field']]}
        else:
          inp_jo={'input': jo['sample_input'], 'output':jo['sample_output']}
        if 'statement' in jo:
          inp_jo['description']=jo['statement']
        else:
          inp_jo['description']=jo['description']
        #print (json.dumps(inp_jo,indent=4))
        try:
          out_jo=await translate(inp_jo, **kwa)
        except Exception as e:
          print ('Error:')
          print (e)
          traceback.print_exc()
          continue
        if not out_jo: continue
        out_jo['description']=inp_jo['description']
        #print(json.dumps(out_jo,indent=4))
        fout.write(out_jo)

if __name__=='__main__':
  asyncio.run(main())
