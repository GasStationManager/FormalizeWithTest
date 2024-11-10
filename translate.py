from litellm import completion
import sys
import jsonlines
import json
import time

content_template="""
You are given a JSON object describing a coding problem.
The "description" field contains the problem description. The {test_field} field contains test cases.
Your task is to translate it into the following in the language 
lean 4: a function signature of the function to be implemented, and 
a formal specification of the requirement the function must satisfy.
The formal specification should further consist of 
1. a definition of a property that takes in the input and output values, and specify that the output value is a correct solution of the problem given the inputs. It should not call the function. 
2. the theorem statement which references the property and the function, and states that for all input values, the output value produced by the function satisfy the above property.
Furthermore, reformat the test cases in the {test_field} field in the input JSON to be a list of strings that 
can be plugged into the property definition. 
Do not try to implement the function or to prove the theorem.
For example, for the task of adding two natural numbers, the function signature would be: 
def add (a b:Nat):Nat 
And the theorem statement would be: 
def add_prop (a b out:Nat): a+b=out 
theorem add_spec (a b:Nat): add_prop a b (add a b)
And the test cases should be in the format "1 1 2"
Make sure that each test case can be plugged into the property, e.g. add_prop 1 1 2.
Again, in the body of the property definition do not call the function.
The body of the property definition should be complete: no 'sorry's, and if you need to make helper
functions, do so and do not put 'sorry' in their bodies.
If you need to use arr[i] to access element of array or list at index i, and you have not yet established
that i is a valid index, you may use arr[i]? notation to return an Option value, 
or arr[i]! notation to leave the proof obligation to the future prover.

Format your output as a JSON Object:
{{
  "function_signature": "def add (a b:Nat):Nat",
  "property_name": "add_prop",
  "property_def": "def add_prop (a b out:Nat): a+b=out",
  "theorem_signature": "theorem add_spec (a b:Nat): add_prop a b (add a b)",
  "tests": ["1 1 2", "1 2 3"]
}}

Any helper function definitions goes in "property_def".

If your Lean 4 code contains newline characters, please properly escape them when converting to json.
Similarly, if your test cases contain string data, escape the quote characters.

You are encouraged to reason step by step; put your thoughts in the <Thinking> ... </Thinking> tag,
then put the final (JSON) output in the <Result> ... </Result> tag.

START OF INPUT
{input_json}
END OF INPUT

START OF OUTPUT
"""



def translate(inp_json, test_field='"input" and "output"'):
  response = completion(
    model="anthropic/claude-3-5-sonnet-20241022", #0620,   #claude-3-sonnet-20240229
    messages=[
        {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
        {"role": "user", "content": content_template.format(input_json=inp_json, test_field=test_field)}
    ],
    max_tokens=4096
  )
  resp=response.choices[0].message.content
  print (resp)
  return json.loads(resp.split('</Result>')[0].split('<Result>')[1])




if __name__=='__main__':
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
          out_jo=translate(inp_jo, **kwa)
        except Exception as e:
          print ('Error:')
          print (e)
          continue
        out_jo['description']=inp_jo['description']
        #print(json.dumps(out_jo,indent=4))
        fout.write(out_jo)

