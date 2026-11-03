# prim_range is not defined

```{code-cell}
from pxr import Usd
stage = Usd.Stage.CreateInMemory()
stage.DefinePrim("/World/Environment")
it = iter(Usd.PrimRange.Stage(stage))
for prim in it:
    if prim.GetName() == "Environment":
        prim_range.PruneChildren()
```
