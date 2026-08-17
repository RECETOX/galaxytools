import re
import math
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from scipy.stats import rankdata
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

"""
Utility functions for computing Pearson correlation between feature intensities and dilution factors.
"""



# the weakest part of this program is the parsing of the dilution factor from the column name.
def dilution_to_concentration(colname: str) -> float:
    """
    Extract the dilution factor from a column name and convert it to a
    relative concentration.
    """

    name = colname.lower()

    # non-dilute = 1.0 dilution factor
    if "non" in name and "dilute" in name:
        return 1.0

    # column name ends with an underscore followed by digits its a dilution factor -> convert it to a relative concentration
    match = re.search(r"_(\d+)\s*$", colname)
    if match:
        if float(match.group(1)) == 0:
            raise ValueError(f"Dilution factor cannot be zero in column: {colname}")
        else:
            factor = float(match.group(1))
            return 1.0 / factor

    raise ValueError(f"Could not parse dilution factor from column: {colname}")



def load_intensity_table(input_path: str, id_col: str = "id"):
    """
    Loads the dilution-series tab delimited intensity table after feature alignment.

    Returns:
      intensity_table_df: full DataFrame as read from disk (id_col kept as a column)
      concentrations    : np.ndarray of relative concentrations, aligned with qc_cols
      intensity_array   : np.ndarray (n_features, n_samples) of raw intensities
    """

    # load the intensity table
    intensity_table_df = pd.read_csv(input_path, sep="\t")
    if id_col.isdigit():
        id_col = intensity_table_df.columns[int(id_col) - 1]

    if id_col not in intensity_table_df.columns:
        raise ValueError(
            f"Expected an '{id_col}' column, found columns: {list(intensity_table_df.columns)}. "
        )

    # parse the QC sample columns and their corresponding concentrations
    qc_cols = [c for c in intensity_table_df.columns if c != id_col]
    concentrations = np.array([dilution_to_concentration(c) for c in qc_cols])
    print("Parsed concentrations:")
    for col, val in zip(qc_cols, concentrations):
        print(f"  {col:25s} -> {val}")

    # convert the intensity table to a numpy array for faster computation of correlation coefficients
    intensity_array = intensity_table_df[qc_cols].to_numpy(dtype=float)
    return intensity_table_df, concentrations, intensity_array



def compute_observed_r_and_p(intensity_array: np.ndarray, dilution_array: np.ndarray, correlation_type: str):
    """
    Pearson or Spearman r and p-value for every feature of intensity_array against dilution_array.

    Returns:
      r_values: np.ndarray of shape (n_features,)
      p_values: np.ndarray of shape (n_features,)
    """

    # define output arrays
    n_features = intensity_array.shape[0]
    r_values = np.empty(n_features)
    p_values = np.empty(n_features)

    # compute r and p for each feature intensity against the dilution vector
    for i in range(n_features):
        intensities = intensity_array[i, :]
        if np.isnan(intensities).any():
            r_values[i] = np.nan
            p_values[i] = np.nan
            continue
        if correlation_type == "pearson":
            r, p = pearsonr(dilution_array, intensities)
        elif correlation_type == "spearman":
            r, p = spearmanr(dilution_array, intensities)
        else:
            raise ValueError(
                f"Unsupported correlation_type: {correlation_type!r}. "
                "Use 'pearson' or 'spearman'."
            )

        r_values[i] = r
        p_values[i] = p

    return r_values, p_values



def compute_r_vector_fast(
    intensity_array: np.ndarray,
    dilution_array: np.ndarray,
    correlation_type: str = "pearson",
) -> np.ndarray:
    """
    Vectorized Pearson or Spearman r for every feature of intensity_array against
    dilution_array for faster computation during permutations. Returns vector of r values.

    Returns:
      r: np.ndarray of shape (n_features,)
    """
    intensity_array = np.asarray(intensity_array, dtype=float)
    dil_arr = np.asarray(dilution_array, dtype=float)

    if correlation_type == "spearman":
        dil_arr = rankdata(dil_arr)
        intensity_array = rankdata(intensity_array, axis=1, nan_policy="omit")
    elif correlation_type != "pearson":
        raise ValueError(
            f"Unsupported correlation_type: {correlation_type!r}. "
            "Use 'pearson' or 'spearman'."
        )

    # compute centered dilution vector and its norm
    dil_c = dil_arr - dil_arr.mean()
    dil_norm = np.sqrt((dil_c ** 2).sum())

    # compute centered intensity array
    valid_rows = ~np.isnan(intensity_array).any(axis=1)
    row_mean = np.nanmean(intensity_array, axis=1, keepdims=True)
    int_c = intensity_array - row_mean

    # compute ||y|| for each row
    int_norm = np.sqrt(np.nansum(int_c ** 2, axis=1))
    y_norm_safe = np.where((int_norm == 0) | ~valid_rows, np.nan, int_norm)

    # compute covariance of each row with the dilution vector, then r = cov / (||x|| * ||y||)
    cov = np.nansum(int_c * dil_c[None, :], axis=1)
    r = cov / (dil_norm * y_norm_safe)

    return r



def permutation_null_r(intensity_array: np.ndarray,
                        concentrations: np.ndarray,
                        n_permutations: int = 1000,
                        random_state: int = 0,
                        correlation_type: str = "pearson") -> np.ndarray:
    """
    Empirical null distribution of Pearson r: shuffle which concentration
    label goes with which sample n_permutations times, recomputing r for
    every feature (row) each time.

    Returns:
        null_r_pooled: np.ndarray of shape (n_permutations * n_features,)
    """

    # set up random number generator and output array
    rng = np.random.default_rng(random_state)
    n_features, n_samples = intensity_array.shape
    null_r = np.empty((n_permutations, n_features), dtype=float)

    # check if requested number of permutations exceeds the number of unique orderings
    n_unique_perms = math.factorial(n_samples)
    if n_permutations > n_unique_perms:
        print(f"Note: requested {n_permutations} permutations but only "
              f"{n_unique_perms} unique orderings exist for {n_samples} "
              f"samples. Consider enumerating all of them exactly instead "
              f"of random sampling (see exact_permutation_null_r).")

    # compute null r for each permutation
    for i in range(n_permutations):
        permuted_concentrations = rng.permutation(concentrations)
        null_r[i, :] = compute_r_vector_fast(
            intensity_array,
            permuted_concentrations,
            correlation_type=correlation_type,
        )

    return null_r.ravel()



def empirical_fdr_curve(observed_r: np.ndarray,
                         null_r_pooled: np.ndarray,
                         n_permutations: int,
                         thresholds_to_try: np.ndarray = None,
                         min_null_count: int = 10):
    """
    Compute the empirical FDR curve based on observed r values and pooled null r values.
    
    Returns:
      fdr_df: pd.DataFrame with columns:
        - threshold: the threshold values
        - n_obs_above: the number of observed features with r >= threshold
        - n_null_above_pooled: the number of null features with r >= threshold
        - expected_null_above: the expected number of null features with r >= threshold
        - FDR: the empirical FDR at each threshold
        - FDR_monotone: the monotonized FDR at each threshold
    """

    # define thresholds if not provided
    if thresholds_to_try is None:
        print("No thresholds provided, using default grid of 501 points from 0 to 1.")
        thresholds_to_try = np.linspace(0, 1, 501)

    # compute counts of observed and null r values above each threshold
    n_obs_above = np.array([(observed_r >= t).sum() for t in thresholds_to_try])
    n_null_above = np.array([(null_r_pooled >= t).sum() for t in thresholds_to_try])
    expected_null_above = n_null_above / n_permutations

    # compute FDR, handling division by zero 
    with np.errstate(divide="ignore", invalid="ignore"):
        fdr = expected_null_above / n_obs_above
    fdr = np.where(n_obs_above == 0, np.nan, fdr)
    fdr = np.minimum(fdr, 1.0)

    # mask out FDR estimates as NaN if they are based on too few pooled null hits
    reliable = n_null_above >= min_null_count 
    fdr_reliable = np.where(reliable, fdr, np.nan)

    # Step-down monotonization: FDR(t) = min over all t'' <= t
    fdr_monotone = np.full_like(fdr, np.nan)
    running_min = np.inf
    for i in range(len(thresholds_to_try)):
        if reliable[i] and not np.isnan(fdr_reliable[i]):
            running_min = min(running_min, fdr_reliable[i])
        fdr_monotone[i] = running_min if np.isfinite(running_min) else np.nan

    # return a DataFrame with the results
    return pd.DataFrame({
        "threshold": thresholds_to_try,
        "n_obs_above": n_obs_above,
        "n_null_above_pooled": n_null_above,
        "expected_null_above": expected_null_above,
        "FDR": fdr,
        "FDR_monotone": fdr_monotone,
    })



def permutation_based_fdr(
    int_table,
    concentrations,
    n_permutations,
    random_state,
    observed_r,
    correlation_type: str = "pearson",
):
    """
    Perform permutation-based FDR estimation by computing the null distribution of r values and the empirical FDR curve.

    Returns:
      null_r_pooled: pooled null r values from permutations
      fdr_df       : DataFrame containing the empirical FDR curve
    """

    null_r_pooled = permutation_null_r(
        int_table,
        concentrations,
        n_permutations=n_permutations,
        random_state=random_state,
        correlation_type=correlation_type,
    )

    # compute empirical FDR curve
    fdr_df = empirical_fdr_curve(
        observed_r,
        null_r_pooled,
        n_permutations=n_permutations,
    )

    return null_r_pooled, fdr_df



def select_threshold(fdr_df: pd.DataFrame, target_fdr: float = 0.05) -> float:
    """
    Pick the smallest r threshold such that the monotonized FDR is still
    <= target_fdr (most permissive threshold meeting the FDR constraint).

    Returns:
      threshold: the selected r threshold
      valid_fdr_values: DataFrame with valid FDR values
    """

    # filter out thresholds where FDR could not be computed
    valid_fdr_values = fdr_df.dropna(subset=["FDR_monotone"])
    if valid_fdr_values.empty:
        raise ValueError("FDR could not be computed at any threshold. "
                          "Check your threshold grid and input data.")
    
    # select the smallest threshold where FDR_monotone <= target_fdr
    fdr_monotone_under_target_fdr = valid_fdr_values[valid_fdr_values["FDR_monotone"] <= target_fdr]

    # if no thresholds meet the target FDR, warn and return the best achievable threshold
    if fdr_monotone_under_target_fdr.empty:
        best = valid_fdr_values.loc[valid_fdr_values["FDR_monotone"].idxmin()]
        print(f"Warning: no threshold achieves FDR <= {target_fdr}. "
              f"Best achievable FDR = {best['FDR_monotone']:.3f} at "
              f"r >= {best['threshold']:.3f}.")
        return float(best["threshold"]), valid_fdr_values
    
    return float(fdr_monotone_under_target_fdr["threshold"].min()), valid_fdr_values



def plot_diagnostic(observed_r, null_r_pooled, fdr_df, threshold, target_fdr, plot_path, valid_fdr_values: pd.DataFrame):
    """
    Generate a diagnostic plot showing the observed and null distributions of Pearson r values,
    as well as the empirical FDR curve and the selected threshold.
    """

    fdr_monotone_under_target_fdr = valid_fdr_values[valid_fdr_values["FDR_monotone"] <= target_fdr]
    if fdr_monotone_under_target_fdr.empty:
            best = valid_fdr_values.loc[valid_fdr_values["FDR_monotone"].idxmin()]
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
            axes[0].hist(observed_r, bins=60, density=True, alpha=0.6, label="Observed R")
            axes[0].hist(null_r_pooled, bins=60, density=True, alpha=0.6, label="Permutation null")
            axes[0].axvline(threshold, color="red", ls="--", label=f"Best achievable FDR: {best['FDR_monotone']:.3f}, cutoff = {threshold:.2f}")
            axes[0].set_xlabel("pearson_r")
            axes[0].set_ylabel("Density")
            axes[0].legend()
            axes[0].set_title("Observed vs null pearson r distributions")

            axes[1].plot(fdr_df["threshold"], fdr_df["FDR_monotone"])
            axes[1].axhline(best['FDR_monotone'], color="grey", ls=":")
            axes[1].axvline(threshold, color="red", ls="--")
            axes[1].set_xlabel("pearson_r threshold")
            axes[1].set_ylabel("Empirical FDR")
            axes[1].set_title("FDR vs pearson_r threshold")
            axes[1].set_ylim(0, 1)

            fig.tight_layout()
            fig.savefig(plot_path, dpi=600)
            print(f"Saved diagnostic plot to {plot_path}")
    else:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
            axes[0].hist(observed_r, bins=60, density=True, alpha=0.6, label="Observed R")
            axes[0].hist(null_r_pooled, bins=60, density=True, alpha=0.6, label="Permutation null")
            axes[0].axvline(threshold, color="red", ls="--", label=f"FDR≤{target_fdr:.0%} cutoff = {threshold:.2f}")
            axes[0].set_xlabel("pearson_r")
            axes[0].set_ylabel("Density")
            axes[0].legend()
            axes[0].set_title("Observed vs null pearson r distributions")

            axes[1].plot(fdr_df["threshold"], fdr_df["FDR_monotone"])
            axes[1].axhline(target_fdr, color="grey", ls=":")
            axes[1].axvline(threshold, color="red", ls="--")
            axes[1].set_xlabel("pearson_r threshold")
            axes[1].set_ylabel("Empirical FDR")
            axes[1].set_title("FDR vs pearson_r threshold")
            axes[1].set_ylim(0, 1)

            fig.tight_layout()
            fig.savefig(plot_path, dpi=600)
            print(f"Saved diagnostic plot to {plot_path}")