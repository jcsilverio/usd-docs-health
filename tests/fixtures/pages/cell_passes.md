# Cell passes

```{code-cell}
from pxr import Usd
stage = Usd.Stage.CreateInMemory()
print(stage.GetPseudoRoot().GetPath())
```
