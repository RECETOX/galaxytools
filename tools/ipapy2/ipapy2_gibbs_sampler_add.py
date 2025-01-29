import os

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

    if args.zs and args.zs.lower() != "none" and os.path.isfile(args.zs):
        zs = []
        with open(args.zs, "r") as f:
            for line in f:
                zs.append(int(line.strip()))

    else:
        zs = None
    zs = ipa.Gibbs_sampler_add(
        df,
        annotations,
        noits=args.noits,
        burn=args.burn,
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

    if args.all_out:
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
        help="A csv file containing the MS1 data. Ideally obtained from map_isotope_patterns",
    )
    parser.add_argument(
        "--annotations",
        type=str,
        required=True,
        help=""" a dictionary containing all the possible annotations for the
                measured features. The keys of the dictionary are the unique
                ids for the features present in df. For each feature, the
                annotations are summarized in a A csv file. Output of
                functions MS1annotation(), MS1annotation_Parallel(),
                MSMSannotation() or MSMSannotation_Parallel""",
    )
    parser.add_argument(
        "--noits",
        type=int,
        help="number of iterations if the Gibbs sampler to be run",
    )
    parser.add_argument(
        "--burn",
        type=int,
        default=None,
        help="""number of iterations to be ignored when computing posterior
          probabilities. If None, is set to 10% of total iterations""",
    )
    parser.add_argument(
        "--delta_add",
        type=float,
        default=1,
        help="""parameter used when computing the conditional priors. The
               parameter must be positive. The smaller the parameter the more
               weight the adducts connections have on the posterior
               probabilities. Default 1.""",
    )
    parser.add_argument(
        "--all_out",
        type=bool,
        default=False,
        help="""logical value. If true the list of assignments found in each
             iteration is returned by the function. Default False.""",
    )
    parser.add_argument(
        "--zs",
        type=str,
        help="""a txt file containing the list of assignments computed in a previous run of the Gibbs sampler. 
        Optional, default None.""",
    )
    parser.add_argument(
        "--zs_out",
        type=str,
        default="gibbs_sample_add_zs.txt",
        help="file name to save the list of assignments computed in the current run of the Gibbs sampler.",
    )
    parser.add_argument(
        "--annotations_out",
        type=str,
        default="gibbs_sample_add_annotations.csv",
    )
    args = parser.parse_args()
    main(args)
