import Lake
open Lake DSL


require smt from git "https://github.com/ufmg-smite/lean-smt.git" @ "main"

def libcpp : String :=
  if System.Platform.isWindows then "libstdc++-6.dll"
  else if System.Platform.isOSX then "libc++.dylib"
  else "libstdc++.so.6"

package «FormalizeWithTest» where
  -- add package configuration options here
  moreLeanArgs := #[s!"--load-dynlib={libcpp}"]
  moreGlobalServerArgs := #[s!"--load-dynlib={libcpp}"]
  require mathlib from git
    "https://github.com/leanprover-community/mathlib4" @ "v4.13.0"

lean_lib «FormalizeWithTest» where
  -- add library configuration options here

@[default_target]
lean_exe «formalizewithtest» where
  root := `Main
