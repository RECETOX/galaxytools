import argparse
import numpy as np
import pandas as pd


def mz_match(marker, peak, ppm):
    return np.abs(marker - peak) <= ((peak + marker) / 2) * ppm * 1e-06


def rt_match(marker, peak, tol):
    return np.abs(marker - peak) <= tol


def find_matches(peaks, markers, ppm, rt_tol):
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
    hits = pd.concat([matched_markers[['formula']].reset_index(drop=True), matched_peaks], axis=1)

     # Calculate mz and rt differences
    hits['mz_diff'] = np.abs(matched_markers['mz'].values - matched_peaks['mz'].values)
    hits['rt_diff'] = np.abs(matched_markers['rt'].values - matched_peaks['rt'].values)

    return hits


def main():
    parser = argparse.ArgumentParser(description='Find matches between peaks and markers.')
    parser.add_argument('--peaks', required=True, help='Path to the peaks parquet file.')
    parser.add_argument('--markers', required=True, help='Path to the markers CSV file.')
    parser.add_argument('--output', required=True, help='Path to the output TSV file.')
    parser.add_argument('--ppm', type=int, default=5, help='PPM tolerance for mz matching.')
    parser.add_argument('--rt_tol', type=int, default=10, help='RT tolerance for rt matching.')
    
    args = parser.parse_args()

    peaks = pd.read_parquet(args.peaks)
    markers = pd.read_csv(args.markers, sep='\t')

    hits = find_matches(peaks, markers, args.ppm, args.rt_tol)

    hits.to_csv(args.output, sep='\t', index=False)


if __name__ == "__main__":
    main()
