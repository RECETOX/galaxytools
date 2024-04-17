import argparse
import sys

from matchms.exporting import save_as_mgf, save_as_msp
from matchms.filtering import add_compound_name, add_fingerprint, add_losses, add_parent_mass, add_precursor_mz,\
    add_retention_index, add_retention_time, clean_compound_name
from matchms.filtering import default_filters, normalize_intensities, reduce_to_number_of_peaks, select_by_mz, \
    select_by_relative_intensity
from matchms.filtering.filter_utils.derive_precursor_mz_and_parent_mass import derive_precursor_mz_from_parent_mass
from matchms.importing import load_from_mgf, load_from_msp


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument("--spectra", type=str, required=True, help="Mass spectra file to be filtered.")
    parser.add_argument("--spectra_format", type=str, required=True, help="Format of spectra file.")
    parser.add_argument("--output", type=str, required=True, help="Filtered mass spectra file.")
    parser.add_argument("-normalise_intensities", action='store_true',
                        help="Normalize intensities of peaks (and losses) to unit height.")
    parser.add_argument("-default_filters", action='store_true',
                        help="Collection of filters that are considered default and that do no require any (factory) arguments.")
    parser.add_argument("-clean_metadata", action='store_true',
                        help="Apply all adding and cleaning filters if possible, so that the spectra have canonical metadata.")
    parser.add_argument("-relative_intensity", action='store_true',
                        help="Keep only peaks within set relative intensity range (keep if to_intensity >= intensity >= from_intensity).")
    parser.add_argument("--from_intensity", type=float, help="Lower bound for intensity filter")
    parser.add_argument("--to_intensity", type=float, help="Upper bound for intensity filter")
    parser.add_argument("-mz_range", action='store_true',
                        help="Keep only peaks between set m/z range (keep if to_mz >= m/z >= from_mz).")
    parser.add_argument("--from_mz", type=float, help="Lower bound for m/z  filter")
    parser.add_argument("--to_mz", type=float, help="Upper bound for m/z  filter")
    parser.add_argument("-derive_precursor_mz_from_parent_mass", action='store_true',
                        help="Derives the precursor_mz from the parent mass and adduct or charge.")
    parser.add_argument("--estimate_from_adduct", type=str, help="estimate from adduct.")
    parser.add_argument("-reduce_to_top_n_peaks", action='store_true',
                        help="reduce to top n peaks filter.")
    parser.add_argument("--n_max", type=int, help="Maximum number of peaks. Remove peaks if more peaks are found.")
    args = parser.parse_args()

    if not (args.normalise_intensities
            or args.default_filters
            or args.clean_metadata
            or args.relative_intensity
            or args.mz_range
            or args.derive_precursor_mz_from_parent_mass
            or args.reduce_to_top_n_peaks):
        raise ValueError('No filter selected.')

    if args.spectra_format == 'msp':
        spectra = list(load_from_msp(args.spectra))
    elif args.queries_format == 'mgf':
        spectra = list(load_from_mgf(args.spectra))
    else:
        raise ValueError(f'File format {args.spectra_format} not supported for mass spectra file.')

    filtered_spectra = []
    for spectrum in spectra:
        if args.normalise_intensities:
            spectrum = normalize_intensities(spectrum)

        if args.default_filters:
            spectrum = default_filters(spectrum)

        if args.clean_metadata:
            filters = [add_compound_name, add_precursor_mz, add_fingerprint, add_losses, add_parent_mass,
                       add_retention_index, add_retention_time, clean_compound_name]
            for metadata_filter in filters:
                spectrum = metadata_filter(spectrum)

        if args.relative_intensity:
            spectrum = select_by_relative_intensity(spectrum, args.from_intensity, args.to_intensity)

        if args.mz_range:
            spectrum = select_by_mz(spectrum, args.from_mz, args.to_mz)

        if args.reduce_to_top_n_peaks:
            spectrum = reduce_to_number_of_peaks(spectrum_in=spectrum, n_max=args.n_max)

        if args.derive_precursor_mz_from_parent_mass:
            spectrum.set("parent_mass", float(spectrum.get('parent_mass')))
            precursor_mz = derive_precursor_mz_from_parent_mass(spectrum, args.estimate_from_adduct)
            spectrum.set("precursor_mz", precursor_mz)

        if spectrum is not None:
            filtered_spectra.append(spectrum)

    if args.spectra_format == 'msp':
        save_as_msp(filtered_spectra, args.output)
    else:
        save_as_mgf(filtered_spectra, args.output)

    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
