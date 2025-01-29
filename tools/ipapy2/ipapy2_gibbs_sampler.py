import argparse
import pandas as pd
from ipaPy2 import ipa


def main(args):
    df = pd.read_csv(args.mapped_isotope_patterns, keep_default_na=False)
    df = df.replace("", None)

    annotations_df = pd.read_csv(args.annotations, keep_default_na=False)
    annotations_df["post"] = annotations_df["post"].replace("", 0)
    annotations_df = annotations_df.replace("", None)
    annotations = {}

    grouped = annotations_df.groupby("peak_id")
    for peak_id, group in grouped:
        annotations[peak_id] = group.drop("peak_id", axis=1)

    if args.zs:
        zs = []
        with open(args.zs, "r") as f:
            for line in f:
                zs.append(int(line.strip()))

    else:
        zs = None

    if args.integrating_mode == "adducts":
        zs = ipa.Gibbs_sampler_add(
            df,
            annotations,
            noits=args.noits,
            burn=args.burn,
            delta_add=args.delta_add,
            all_out=args.all_out,
            zs=zs,
        )
    else:

        Bio = pd.read_csv(args.Bio, keep_default_na=False)

        if args.integrating_mode == "biochemical":
            zs = ipa.Gibbs_sampler_bio(
                df,
                annotations,
                Bio=Bio,
                noits=args.noits,
                burn=args.burn,
                delta_bio=args.delta_bio,
                all_out=args.all_out,
                zs=zs,
            )
        else:
            zs = ipa.Gibbs_sampler_bio_add(
                df,
                annotations,
                Bio=Bio,
                noits=args.noits,
                burn=args.burn,
                delta_bio=args.delta_bio,
                delta_add=args.delta_add,
                all_out=args.all_out,
                zs=zs,
            )

    annotations_flat = pd.DataFrame()
    for peak_id in annotations:
        annotation = annotations[peak_id]
        annotation["peak_id"] = peak_id
        annotations_flat = pd.concat([annotations_flat, annotation])

    annotations_flat.to_csv(args.annotations_out, index=False)

    if args.gibbs_out:
        with open(args.zs_out, "w") as f:
            for s in zs:
                f.write(str(s) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="cluster features before IPA pipeline."
    )
    parser.add_argument(
        "--mapped_isotope_patterns",
        type=str,
        required=True,
        help="a dataframe containing the measured intensities across several samples.",
    )
    parser.add_argument(
        "--annotations",
        type=str,
        required=True,
        help="Default value 0.8. Minimum correlation allowed in each cluster.",
    )
    parser.add_argument(
        "--integrating_mode",
        type=str,
        required=True,
        help="Default value 0.8. Minimum correlation allowed in each cluster.",
    )
    parser.add_argument(
        "--Bio", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--noits",
        type=int,
        help="Default value 1. Maximum difference in RT time between features in the same cluster.",
    )
    parser.add_argument(
        "--burn", type=int, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--delta_bio", type=float, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--delta_add", type=float, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--all_out", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--zs", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--gibbs_out", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--annotations_out",
        type=str,
        default="gibbs_sample_annotations.csv",
        help="a dataframe of clustered features.",
    )
    parser.add_argument("--zs_out", type=str, help="a dataframe of clustered features.")
    args = parser.parse_args()
    main(args)
