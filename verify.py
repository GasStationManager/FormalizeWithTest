import subprocess
import tempfile
import os
import re
import sys
import json
import jsonlines
import copy
import asyncio
import litellm
from LeanTool.leantool import interactive_lean_check,models

#litellm.set_verbose=True

TAC="""repeat (first | rfl | decide | omega | tauto | simp_all | simp_arith | linarith | contradiction | assumption | bv_decide | aesop | smt | constructor | split)"""

PROOF=""":=by 
simp[{prop_name}] 
try {TAC}
try norm_num
try ring_nf
try intros
try {TAC}
"""

OPTIONS="""set_option maxRecDepth 1024\n"""

LLMPROVER=None # set to e.g. 'sonnet' to use models['sonnet']

PROMPT="""Prove the theorem statement by completing the body of its signature below. Your answer should not repeat the signature; i.e. should start with := \n"""


async def verify(prop_name: str,prop_def: str, test_case: str, deps: str='') -> dict:
  print(prop_def)

  #don't need the following if we check for syntax before
  #if '\\n' in prop_def and '\\"' not in prop_def:
  #  prop_def=prop_def.replace ('\\n', '\n')
  #  print('fixed newlines\n'+prop_def)
  if prop_name in test_case:
    test_case=test_case.replace(prop_name, '')
  prop_exp = prop_name + ' ' + test_case
  prop_proof=PROOF.format(prop_name=prop_name, TAC=TAC)
  true_thm_sig="theorem prop_true: "+prop_exp
  true_thm=true_thm_sig+prop_proof+"\n"
  print(true_thm)
  false_thm_sig="theorem prop_false: Not ({})".format(prop_exp)
  false_thm="{} {}\n".format(false_thm_sig,prop_proof)
  print(false_thm)
  prop_def =prop_def.replace ('def', '@[simp] def')
  if len(deps)==0: deps='import Mathlib\nimport Aesop\nimport Smt'

  def check_lean(fname):
            # Run Lean 4 on the temporary file
            result = subprocess.run(["lake","env","lean","--load-dynlib=libstdc++.so.6", "--load-dynlib=.lake/packages/cvc5/.lake/build/lib/libcvc5-1.so", fname], capture_output=True, text=True)
        
            # Check if Lean 4 succeeded (return code 0 means success)
            is_correct = result.returncode == 0
        
            # Extract error messages if the proof failed
            error_message = ""
            error_lines = result.stderr.split('\n') + result.stdout.split('\n')
            for line in error_lines:
                error_message += line + "\n"
                if "error:" in line or "warning: declaration uses 'sorry'" in line:
                    is_correct=False
            return is_correct, error_message

  with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary Lean file
        truef=os.path.join(tmpdir, "true.lean")
        falsef=os.path.join(tmpdir, "false.lean")
        with open(truef, "w") as f:
            f.write(deps+'\n'+prop_def+'\n\n'+OPTIONS+'\n\n'+true_thm)
        with open(falsef, "w") as f:
            f.write(deps+'\n'+prop_def+'\n\n'+OPTIONS+'\n\n'+false_thm)

        for fname in [truef, falsef]:
            print ('proving '+fname)
            is_correct,error_message=check_lean(fname)
            print(error_message)
            status="unknown"
            if is_correct:
              status="pass" if fname==truef else "fail"
              break
        if LLMPROVER is not None and status=="unknown":
          for i,thm in enumerate([true_thm_sig,false_thm_sig]):
            prefix=deps+'\n'+prop_def+'\n\n'+thm
            res=await interactive_lean_check(PROMPT, model=models[LLMPROVER],prefix=prefix)
            is_correct=False
            if 'final_code' in res:
                is_correct, errmsg2=check_lean(prefix+res['final_code'])
                error_message+=f"LLM Proof {i}:\n{errmsg2}\n"
            if is_correct:
                status='pass' if i==0 else 'fail'
                break
        return {
            "status": status,
            "feedback": error_message.strip() if error_message else "Proof checked successfully!"
        }

async def verify_row(row_obj: dict)->dict:
    prop_name=row_obj['property_name'] if 'property_name' in row_obj else row_obj['property_def'].split()[1]
    prop_def=row_obj['property_def']
    deps=row_obj['deps'] if 'deps' in row_obj else ''
    out_obj=copy.deepcopy(row_obj)
    out_obj['test_results']=[]
    out_obj['status']='pass'
    if 'tests' not in row_obj:
      print('Error:the row does not contain a tests field')
      out_obj['status']='unknown'
      return out_obj 
    for t in row_obj['tests']:
      r=await verify(prop_name,prop_def,t, deps)
      out_obj['test_results'].append(r)
    for r in out_obj['test_results']:
      if r['status']=='fail':
        out_obj['status']='fail'
        break
      if r['status']=='unknown':
        out_obj['status']='unknown'
    print(out_obj['status'])
    return out_obj

async def verify_batch(fin, fout):
    with jsonlines.open(fin) as reader:
      with jsonlines.open(fout, mode='w') as writer:
        for jo in reader:
          r=await verify_row(jo)
          writer.write(r)

if __name__=='__main__':
  if len(sys.argv)>1:
    fin=sys.argv[1]
  else:
    fin=sys.stdin
  if len(sys.argv)>2:
    fout=sys.argv[2]
  else:
    fout=sys.stdout
  asyncio.run(verify_batch(fin,fout))
