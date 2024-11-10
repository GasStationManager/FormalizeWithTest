import Lake
open Lake DSL

package «FormalizeWithTest» where
  -- add package configuration options here
  require mathlib from git
    "https://github.com/leanprover-community/mathlib4"
lean_lib «FormalizeWithTest» where
  -- add library configuration options here

@[default_target]
lean_exe «formalizewithtest» where
  root := `Main
