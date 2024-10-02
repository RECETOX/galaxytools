import argparse

import numpy as np
import pandas as pd

def _mean(marker, peak):
    return ((peak + marker) / 2)


def mz_match(marker, peak, ppm):
    return np.abs(marker - peak) <= _mean(marker, peak) * ppm * 1e-06


def rt_match(marker, peak, tol):
    return np.abs(marker - peak) <= tol


def area_match(marker, peak, tol_frac):
    return np.abs(marker - peak) <= tol_frac * _mean(marker, peak)


def sigma_ratio_match(marker, peak, tol_frac):
    return np.abs(marker - peak) <= tol_frac


def find_matches(peaks, markers, ppm, rt_tol, advanced_matching, area_tol_frac, sigma_tol_frac):
    # Create a meshgrid of all combinations of mz and rt values
    marker_mz = markers['mz'].values[:, np.newaxis]
    peak_mz = peaks['mz'].values
    marker_rt = markers['rt'].values[:, np.newaxis]
    peak_rt = peaks['rt'].values

    # Calculate mz and rt matches
    mz_matches = mz_match(marker_mz, peak_mz, ppm)
    rt_matches = rt_match(marker_rt, peak_rt, rt_tol)

    if advanced_matching:
        marker_area = markers['area'].values[:, np.newaxis]
        peak_area = peaks['area'].values
        marker_sigma = markers['sigma'].values[:, np.newaxis]
        peak_sigma = peaks['sd1'].values / peaks['sd2'].values
        area_matches = area_match(marker_area, peak_area, area_tol_frac)
        sigma_ratio_matches = sigma_ratio_match(marker_sigma, peak_sigma, sigma_tol_frac)
    else:
        area_matches = True
        sigma_ratio_matches = True


    # Find the indices where both mz and rt match
    match_indices = np.where(mz_matches & rt_matches & area_matches & sigma_ratio_matches)

    # Create a DataFrame of hits
    matched_markers = markers.iloc[match_indices[0]].reset_index(drop=True)
    matched_peaks = peaks.iloc[match_indices[1]].reset_index(drop=True)
    hits = pd.concat([matched_markers[['formula']].reset_index(drop=True), matched_peaks], axis=1)

    # Calculate mz and rt differences
    hits['mz_diff'] = np.abs(matched_markers['mz'].values - matched_peaks['mz'].values)
    hits['rt_diff'] = np.abs(matched_markers['rt'].values - matched_peaks['rt'].values)
    hits['area_diff'] = np.abs(matched_markers['area'].values - matched_peaks['area'].values)
    return hits


def main():
    parser = argparse.ArgumentParser(description='Find matches between peaks and markers.')
    parser.add_argument('--peaks', required=True, help='Path to the peaks parquet file.')
    parser.add_argument('--markers', required=True, help='Path to the markers CSV file.')
    parser.add_argument('--output', required=True, help='Path to the output TSV file.')
    parser.add_argument('--ppm', type=int, default=5, help='PPM tolerance for mz matching.')
    parser.add_argument('--rt_tol', type=int, default=10, help='RT tolerance for rt matching.')
    parser.add_argument('--advanced_matching', action='store_true', help='Enable advanced matching.')
    parser.add_argument('--area_tol_frac', type=float, default=0.1, help='Fractional tolerance for area matching.')
    parser.add_argument('--sigma_tol_frac', type=float, default=0.1, help='Fractional tolerance for sigma matching.')
    args = parser.parse_args()

    peaks = pd.read_parquet(args.peaks)
    markers = pd.read_csv(args.markers, sep='\t')

    hits = find_matches(peaks, markers, args.ppm, args.rt_tol, args.advanced_matching, args.area_tol_frac, args.sigma_tol_frac)

    hits.to_csv(args.output, sep='\t', index=False)


if __name__ == "__main__":
    main()
