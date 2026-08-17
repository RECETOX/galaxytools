import argparse
from pathlib import Path


"""
Permutation-based empirical null for selecting a Pearson-r threshold in
dilution-series metabolomics data.

Expected input table (one row per feature, one column per QC sample):
id, N_QC_32, N_QC_16, N_QC_8, N_QC_4, N_QC_2, N_QC_non-dilute
where "N" is run identifier and the trailing number is the
dilution factor (32 = diluted 32x, etc.), picked up by regex for
correlation calculation.
"""


from utils import (
    load_intensity_table, compute_observed_r_and_p, select_threshold,
    plot_diagnostic, permutation_based_fdr
)


def run_pipeline(
    input_path: str,
    plot_path: str,
    n_permutations: int,
    target_fdr: float,
    random_state: int,
    id_col: str,
    correlation_type: str = "pearson",
    results_dir: str = ".",
):
    """
    Run the full pipeline of computing observed Pearson correlations, estimating a permutation null, and selecting an empirical FDR threshold.
    """

    # determine canonical "all" and "filtered" filenames inside results_dir
    format = ".tsv"
    base = input_path.stem
    all_path = results_dir / f"{base}_all{format}"
    filtered_path = results_dir / f"{base}_filtered{format}"

    # load the intensity table and parse the dilution factors
    intensity_table_df, concentrations, int_table = load_intensity_table(
        input_path, id_col=id_col
    )

    # compute observed r and p values for each feature against the dilution vector and save to a new output table
    observed_r, observed_p = compute_observed_r_and_p(
        int_table, concentrations, correlation_type=correlation_type
    )
    df_out = intensity_table_df.copy()

    r_col = f"{correlation_type}_r"
    p_col = f"{correlation_type}_p"

    df_out[r_col] = observed_r
    df_out[p_col] = observed_p

    df_out.to_csv(all_path, sep="\t", index=False)
    print(f"Saved observed r/p (all features) to {all_path}")

    null_r_pooled, fdr_df = permutation_based_fdr(
        int_table,
        concentrations,
        n_permutations,
        random_state,
        observed_r,
        correlation_type=correlation_type,
    )

    # select threshold based on target FDR
    threshold, valid_fdr_values = select_threshold(fdr_df, target_fdr=target_fdr)
    filtered_df = df_out[df_out[r_col] >= threshold].copy()
    fdr_monotone_under_target_fdr = valid_fdr_values[valid_fdr_values["FDR_monotone"] <= target_fdr]
    
    if fdr_monotone_under_target_fdr.empty:
        best = valid_fdr_values.loc[valid_fdr_values["FDR_monotone"].idxmin()]
        print(f"Selected threshold at FDR <= {best['FDR_monotone']:.2%}: {threshold:.4f}")
    else:
        print(f"Selected threshold at FDR <= {target_fdr:.2%}: {threshold:.4f}")

    # filter the intensity table to only include features with r >= threshold
    if fdr_monotone_under_target_fdr.empty:
        pass
    else:
        filtered_df.to_csv(filtered_path, sep="\t", index=False)
        print(f"{len(filtered_df)} features with r >= {threshold:.4f} ({len(filtered_df) / len(df_out):.2%} of total {len(df_out)} features)\nSaved filtered intensity table to {filtered_path}.")

    # generate diagnostic plot
    plot_diagnostic(observed_r, null_r_pooled, fdr_df, threshold, target_fdr, plot_path, valid_fdr_values)

    return {
        "threshold": threshold,
        "filtered_path": filtered_path,
        "plot_path": plot_path,
        "fdr_table": fdr_df,
    }



def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute observed Pearson correlations, estimate a permutation null, and select an empirical FDR threshold."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the tab-delimited intensity matrix input file.",
    )

    parser.add_argument(
        "-p",
        "--plot",
        default="r_threshold_diagnostic.png",
        help="Path to save the diagnostic plot.",
    )

    parser.add_argument(
        "-c",
        "--correlation-type",
        type=str,
        default="pearson",
        help="Choose type of the correlation coefficient. Options:"
        "- Pearson correlation (pearson), default"
        "- Spearman correlation (spearman)"
        )

    parser.add_argument(
        "-n",
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of random permutations to generate the null distribution.",
    )

    parser.add_argument(
        "-f",
        "--target-fdr",
        type=float,
        default=0.05,
        help="Target empirical false discovery rate for threshold selection.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for permutation sampling.",
    )

    parser.add_argument(
        "--id-col",
        default="id",
        help="Name of the feature identifier column in the input table.",
    )

    parser.add_argument(
        "--results-dir",
        default=None,
        help="Directory where output files will be saved. Defaults to a subfolder next to the input file.",
    )

    return parser.parse_args()



def main():
    args = parse_args()
    run_pipeline(
        input_path=Path(args.input),
        plot_path=Path(args.plot),
        n_permutations=args.n_permutations,
        target_fdr=args.target_fdr,
        random_state=args.seed,
        id_col=args.id_col,
        results_dir=Path(args.results_dir),
        correlation_type=args.correlation_type,
    )



if __name__ == "__main__":
    main()