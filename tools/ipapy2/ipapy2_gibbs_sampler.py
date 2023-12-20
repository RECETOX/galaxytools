import argparse
import sys
import os
import pandas as pd
from ipaPy2 import ipa


def main(argv):
    parser = argparse.ArgumentParser(description="cluster features before IPA pipeline.")
    parser.add_argument("--MS1_table", type=str, required=True, help="a dataframe containing the measured intensities across several samples.")
    parser.add_argument("--annotations", type=str, required=True, help="Default value 0.8. Minimum correlation allowed in each cluster.")
    parser.add_argument("--integrating_mode", type=str, required=True, help="Default value 0.8. Minimum correlation allowed in each cluster.")
    parser.add_argument("--Bio", type=str, required=True, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--noits", type=int, required=True, help="Default value 1. Maximum difference in RT time between features in the same cluster.")
    parser.add_argument("--burn", type=int, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--delta_bio", type=float, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--delta_add", type=float, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--all_out", type=str, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--zs", type=str, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--gibbs_out", type=str, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("--annotations_out", type=str, required=True, help="a dataframe of clustered features.")
    parser.add_argument("--zs_out", type=str, help="a dataframe of clustered features.")
    args = parser.parse_args()

    df = pd.read_csv(args.MS1_table, keep_default_na=False)
    df = df.replace('', None)

    annotations_df = pd.read_csv(args.annotations, keep_default_na=False)
    annotations_df = annotations_df.replace('', None)
    annotations = {}
    keys = set(annotations_df["peak_id"])
    for i in keys:
        annotations[i] = annotations_df[annotations_df["peak_id"] == i].drop('peak_id', axis=1)

    if args.zs:
        zs = []
        with open(args.zs, 'r') as f:
            for line in f:
                zs.append(int(line.strip()))
    else: 
        zs = None

    if args.integrating_mode == "adducts":
        zs = ipa.Gibbs_sampler_add(df, annotations, noits=args.noits, burn=args.burn, delta_add=args.delta_add, all_out=args.all_out, zs=zs)
    else:
        Bio = pd.read_csv(args.Bio, keep_default_na=False)
        if args.integrating_mode == "biochemical":
            zs = ipa.Gibbs_sampler_bio(df, annotations, Bio=Bio, noits=args.noits, burn=burn, delta_bio=args.delta_bio, all_out=args.all_out, zs=zs)
        else:
            zs = ipa.Gibbs_sampler_bio_add(df, annotations, Bio=Bio, noits=args.noits, burn=burn, delta_bio=args.delta_bio, delta_add=args.delta_add, all_out=args.all_out, zs=zs)

    annotations_flat = pd.DataFrame()
    for peak_id in annotations:
        annotation = annotations[peak_id]
        annotation["peak_id"] = peak_id
        annotations_flat = pd.concat([annotations_flat, annotation])
        
    annotations_flat.to_csv(args.annotations_out, index=False)
    if args.gibbs_out:
        with open(args.zs_out, 'w') as f:
            for s in zs:
                f.write(str(s) +"\n")


if __name__ == '__main__':
    main(argv=sys.argv[1:])