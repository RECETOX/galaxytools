import argparse
import os

import pandas as pd
from ipaPy2 import ipa


def main(args):
    df = pd.read_csv(args.mapped_isotope_patterns, keep_default_na=False)
    df = df.replace("", None)
    dfMS2 = pd.read_csv(args.MS2_fragmentation_data, keep_default_na=False)
    dfMS2 = dfMS2.replace('', None)
    all_adducts = pd.read_csv(args.all_adducts, keep_default_na=False)
    all_adducts = all_adducts.replace("", None)
    MS2_DB = pd.read_csv(args.MS2_DB, keep_default_na=False)
    MS2_DB = MS2_DB.replace("", None)

    ncores = int(os.environ.get("GALAXY_SLOTS")) if args.ncores is None else args.ncores
    ppmthr = args.ppmthr if args.ppmthr else 2 * args.ppm

    annotations = ipa.MSMSannotation(
        df, 
        dfMS2, 
        all_adducts, 
        MS2_DB, 
        ppm=args.ppm, 
        ratiosd=args.ratiosd, 
        ppmunk=args.ppmunk, 
        ratiounk=args.ratiounk, 
        ppmthr=ppmthr, 
        pRTNone=args.pRTNone, 
        pRTout=args.pRTout, 
        mzdCS=args.mzdCS, 
        ppmCS=args.ppmCS, 
        CSunk=args.CSunk, 
        evfilt=args.evfilt, 
        ncores=ncores
    )
    annotations_flat = pd.DataFrame()
    for peak_id in annotations:
        annotation = annotations[peak_id]
        annotation["peak_id"] = peak_id
        annotations_flat = pd.concat([annotations_flat, annotation])
    annotations_file = (
        args.MS2_annotations if args.MS2_annotations else "MS2_annotations.csv"
    )
    annotations_flat.to_csv(annotations_file, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mapped_isotope_patterns",
        type=str,
        required=True,
        help="A csv file containing the MS1 data. Ideally obtained from map_isotope_patterns",
    )
    parser.add_argument(
        "--MS2_fragmentation_data",
        type=str,
        required=True,
        help="A csv file containing the MS2 fragmentation data",
    )
    parser.add_argument(
        "--all_adducts",
        type=str,
        required=True,
        help="A csv file containing the information on all the possible adducts given the database. Ideally obtained from compute_all_adducts",
    )
    parser.add_argument(
        "--MS2_DB",
        type=str,
        required=True,
        help="A csv file containing the MS2 database",
    )
    parser.add_argument(
        "--ppm",
        type=float,
        required=True,
        help="accuracy of the MS instrument used.",
    )
    parser.add_argument(
        "me",
        type=float,
        default=5.48579909065e-04,
        help="accurate mass of the electron. Default 5.48579909065e-04",

    )
    parser.add_argument(
        "--ratiosd",
        type=float,
        default=0.9,
        help="acceptable ratio between predicted intensity and observed intensity of isotopes.",
    )
    parser.add_argument(
        "--ppmunk",
        type=float,
        help="pm associated to the 'unknown' annotation. If not provided equal to ppm.",
    )
    parser.add_argument(
        "--ratiounk",
        type=float,
        default=0.5,
        help="isotope ratio associated to the 'unknown' annotation.",
    )
    parser.add_argument(
        "--ppmthr",
        type=float,
        help="maximum ppm possible for the annotations. if not provided equal to 2*ppm.",
    )
    parser.add_argument(
        "--pRTNone",
        type=float,
        default=0.8,
        help="multiplicative factor for the RT if no RTrange present in the database.",
    )
    parser.add_argument(
        "--pRTout",
        type=float,
        default=0.4,
        help="multiplicative factor for the RT if measured RT is outside the RTrange present in the database.",
    )
    parser.add_argument(
        "mzdCS",
        type=int,
        default=0,
        help="""maximum mz difference allowed when computing cosine similarity
           scores. If one wants to use this parameter instead of ppmCS, this
           must be set to 0. Default 0.""",
    )
    parser.add_argument(
        "ppmCS",
        type=int,
        default=10,
        help="""maximum ppm allowed when computing cosine similarity scores.
           If one wants to use this parameter instead of mzdCS, this must be
           set to 0. Default 10.""",
    )
    parser.add_argument(
        "CSunk",
        type=float,
        default=0.7,
        help="""cosine similarity score associated with the 'unknown' annotation.
            Default 0.7""",
    )
    parser.add_argument(
        "--evfilt",
        type=bool,
        default=False,
        help="""Default value False. If true, only spectrum acquired with the same
            collision energy are considered.""",
    )
    parser.add_argument(
        "--MS2_annotations",
        type=str,
        help="MS2 annotation file for outputting results.",
    )
    parser.add_argument(
        "--ncores",
        type=int,
        default=None,
        help="number of cores to use for the computation.",
    )
    args = parser.parse_args()
    main(args)
