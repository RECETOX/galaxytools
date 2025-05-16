import argparse
from typing import Tuple

import numpy as np
import pandas as pd


class LoadDataAction(argparse.Action):
    """
    Custom argparse action to load data from a file into a pandas DataFrame.
    Supports CSV, TSV, and Parquet file formats.
    """
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Tuple[str, str], option_string: str = None) -> None:
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            df = pd.read_csv(file_path)
        elif file_extension in ["tsv", "tabular"]:
            df = pd.read_csv(file_path, sep="\t")
        elif file_extension == "parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, df)


def mz_match(marker: np.ndarray, peak: np.ndarray, ppm: int) -> np.ndarray:
    """
    Check if the mass-to-charge ratio (m/z) of markers and peaks match within a given PPM tolerance.

    Args:
        marker (np.ndarray): Array of marker m/z values.
        peak (np.ndarray): Array of peak m/z values.
        ppm (int): PPM tolerance for matching.

    Returns:
        np.ndarray: Boolean array indicating matches.
    """
    return np.abs(marker - peak) <= ((peak + marker) / 2) * ppm * 1e-06


def rt_match(marker: np.ndarray, peak: np.ndarray, tol: int) -> np.ndarray:
    """
    Check if the retention time (rt) of markers and peaks match within a given tolerance.

    Args:
        marker (np.ndarray): Array of marker retention times.
        peak (np.ndarray): Array of peak retention times.
        tol (int): Retention time tolerance for matching.

    Returns:
        np.ndarray: Boolean array indicating matches.
    """
    return np.abs(marker - peak) <= tol


def find_matches(peaks: pd.DataFrame, markers: pd.DataFrame, ppm: int, rt_tol: int) -> pd.DataFrame:
    """
    Find matches between peaks and markers based on m/z and retention time tolerances.

    Args:
        peaks (pd.DataFrame): DataFrame containing peak data with 'mz' and 'rt' columns.
        markers (pd.DataFrame): DataFrame containing marker data with 'mz' and 'rt' columns.
        ppm (int): PPM tolerance for m/z matching.
        rt_tol (int): Retention time tolerance for rt matching.

    Returns:
        pd.DataFrame: DataFrame containing matched rows with all columns from peaks and markers.
    """
    # Create a meshgrid of all combinations of mz and rt values
    marker_mz = markers['mz'].values[:, np.newaxis]
    peak_mz = peaks['mz'].values
    marker_rt = markers['rt'].values[:, np.newaxis]
    peak_rt = peaks['rt'].values

    # Calculate mz and rt matches
    mz_matches = mz_match(marker_mz, peak_mz, ppm)
    rt_matches = rt_match(marker_rt, peak_rt, rt_tol)

    # Find the indices where both mz and rt match
    match_indices = np.where(mz_matches & rt_matches)

    # Create a DataFrame of hits
    matched_markers = markers.iloc[match_indices[0]].reset_index(drop=True)
    matched_peaks = peaks.iloc[match_indices[1]].reset_index(drop=True)

    # Calculate mz and rt differences
    matched_markers['mz_diff'] = np.abs(matched_markers['mz'].values - matched_peaks['mz'].values)
    matched_markers['rt_diff'] = np.abs(matched_markers['rt'].values - matched_peaks['rt'].values)

    # Drop mz and rt columns from the marker table
    matched_markers = matched_markers.drop(columns=['mz', 'rt'])

    # Combine all columns from peaks and markers
    hits = pd.concat([matched_markers.reset_index(drop=True), matched_peaks.reset_index(drop=True)], axis=1)
    return hits


def main() -> None:
    """
    Main function to parse arguments, find matches between peaks and markers, and save the results.
    """
    parser = argparse.ArgumentParser(description='Find matches between peaks and markers.')
    parser.add_argument('--peaks', required=True, nargs=2, action=LoadDataAction, help='Path to the peaks file and its format (e.g., "file.parquet parquet").')
    parser.add_argument('--markers', required=True, nargs=2, action=LoadDataAction, help='Path to the markers file and its format (e.g., "file.tsv tsv").')
    parser.add_argument('--output', required=True, help='Path to the output TSV file.')
    parser.add_argument('--ppm', type=int, default=5, help='PPM tolerance for mz matching.')
    parser.add_argument('--rt_tol', type=int, default=10, help='RT tolerance for rt matching.')
    args = parser.parse_args()

    hits = find_matches(args.peaks, args.markers, args.ppm, args.rt_tol)

    hits.to_csv(args.output, sep='\t', index=False)


if __name__ == "__main__":
    main()
