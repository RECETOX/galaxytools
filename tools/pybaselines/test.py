import pandas as pd
from pybaselines import Baseline
import numpy as np

def correct_baseline(group):
    """Apply baseline correction to a single group."""
    group = group.sort_values(by="rt").reset_index(drop=True)

    x_data = group.rt.values
    y_data = group.intensity.values

    base_fitter = Baseline(x_data)
    baseline, params = base_fitter.lsrpls(y_data, lam=600, max_iter=30, tol=0.1)

    group["intensity"] = np.maximum(np.zeros_like(y_data), y_data - baseline)
    return group

# Read and group by group_number, then apply baseline correction to each group
eics: pd.DataFrame = pd.read_parquet("test-data/input.parquet")
corrected = eics.groupby("group_number", group_keys=False).apply(correct_baseline)

# Reset index on final result
corrected = corrected.reset_index(drop=True)
corrected.to_parquet("test-data/result.parquet")