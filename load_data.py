
from datasets import load_dataset

import sys

def load_hackercup(out_fname, year='2023'):
    hackercupai_ds = load_dataset("hackercupai/hackercup", cache_dir="datasets")['full']
    hackercupai_ds = hackercupai_ds.filter(lambda example: all([example[col] for col in ["input", "output"]]))
    hackercupai_ds = hackercupai_ds.filter(lambda example: example['year']==year)
    hackercupai_ds.to_json(out_fname)


if __name__=='__main__':
  if len(sys.argv)>2:
    year=sys.argv[2]
  else:
    year='2023'
  load_hackercup(sys.argv[1], year)
