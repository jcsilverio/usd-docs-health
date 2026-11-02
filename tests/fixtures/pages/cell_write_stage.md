# Cell writes a stage

```{code-cell}
from lousd.utils.helperfunctions import create_new_stage
stage = create_new_stage("made_in_temp.usda")
print(stage.GetRootLayer().identifier)
```
