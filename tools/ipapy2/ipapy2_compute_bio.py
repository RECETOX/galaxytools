import argparse
import os
import pandas as pd
from ipaPy2 import ipa


def main(args):
    MS1_DB = pd.read_csv(args.MS1_DB)
    MS1_DB = MS1_DB.replace("", None)

    if args.annotations:
        annotations_df = pd.read_csv(args.annotations, keep_default_na=False)
        annotations_df = annotations_df.replace("", None)
        annotations = {}
        keys = set(annotations_df["peak_id"])
        for i in keys:
            annotations[i] = annotations_df[annotations_df["peak_id"] == i].drop(
                "peak_id", axis=1
            )
    else:
        annotations = None

    if args.biochemical_mode == "connections" and args.connection_list:
        connections = args.connection_list
    else:
        connections = [
            "C3H5NO",
            "C6H12N4O",
            "C4H6N2O2",
            "C4H5NO3",
            "C3H5NOS",
            "C6H10N2O3S2",
            "C5H7NO3",
            "C5H8N2O2",
            "C2H3NO",
            "C6H7N3O",
            "C6H11NO",
            "C6H11NO",
            "C6H12N2O",
            "C5H9NOS",
            "C9H9NO",
            "C5H7NO",
            "C3H5NO2",
            "C4H7NO2",
            "C11H10N2O",
            "C9H9NO2",
            "C5H9NO",
            "C4H4O2",
            "C3H5O",
            "C10H12N5O6P",
            "C10H15N2O3S",
            "C10H14N2O2S",
            "CH2ON",
            "C21H34N7O16P3S",
            "C21H33N7O15P3S",
            "C10H15N3O5S",
            "C5H7",
            "C3H2O3",
            "C16H30O",
            "C8H8NO5P",
            "CH3N2O",
            "C5H4N5",
            "C10H11N5O3",
            "C10H13N5O9P2",
            "C10H12N5O6P",
            "C9H13N3O10P2",
            "C9H12N3O7P",
            "C4H4N3O",
            "C10H13N5O10P2",
            "C10H12N5O7P",
            "C5H4N5O",
            "C10H11N5O4",
            "C10H14N2O10P2",
            "C10H12N2O4",
            "C5H5N2O2",
            "C10H13N2O7P",
            "C9H12N2O11P2",
            "C9H11N2O8P",
            "C4H3N2O2",
            "C9H10N2O5",
            "C2H3O2",
            "C2H2O",
            "C2H2",
            "CO2",
            "CHO2",
            "H2O",
            "H3O6P2",
            "C2H4",
            "CO",
            "C2O2",
            "H2",
            "O",
            "P",
            "C2H2O",
            "CH2",
            "HPO3",
            "NH2",
            "PP",
            "NH",
            "SO3",
            "N",
            "C6H10O5",
            "C6H10O6",
            "C5H8O4",
            "C12H20O11",
            "C6H11O8P",
            "C6H8O6",
            "C6H10O5",
            "C18H30O15",
        ]

    Bio = ipa.Compute_Bio(
        MS1_DB,
        annotations=annotations,
        mode=args.biochemical_mode,
        connections=connections,
        ncores=int(os.environ.get("GALAXY_SLOTS")),
    )
    Bio.to_csv(args.compute_bio_output, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="cluster features before IPA pipeline."
    )
    parser.add_argument(
        "--MS1_DB",
        type=str,
        required=True,
        help="a dataframe containing the measured intensities across several samples.",
    )
    parser.add_argument(
        "--annotations",
        type=str,
        help="a dataframe containing the annotations of the features.",
    )
    parser.add_argument(
        "--biochemical_mode",
        type=str,
        required=True,
        help="Default value 1. Maximum difference in RT time between features in the same cluster.",
    )
    parser.add_argument(
        "--connection_list", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--compute_bio_output", type=str, required=True, help="Output file path for the dataframe."
    )
    args = parser.parse_args()

    main(args)
