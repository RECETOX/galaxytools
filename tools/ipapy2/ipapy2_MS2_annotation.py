import argparse


from ipaPy2 import ipa
from utils import flattern_annotations, LoadDataAction, StoreOutputAction


def main(
    input_dataset_mapped_isotope_patterns,
    input_dataset_MS2,
    input_dataset_adducts,
    input_dataset_MS2_DB,
    ppm,
    ratiosd,
    ppmunk,
    ratiounk,
    ppmthr,
    pRTNone,
    pRTout,
    mzdCS,
    ppmCS,
    CSunk,
    evfilt,
    output_dataset,
    ncores,
):
    ncores = ncores if ncores else 1
    ppmunk = ppmunk if ppmunk else ppm
    ppmthr = ppmthr if ppmthr else 2 * ppm

    annotations = ipa.MSMSannotation(
        input_dataset_mapped_isotope_patterns,
        input_dataset_MS2,
        input_dataset_adducts,
        input_dataset_MS2_DB,
        ppm=ppm,
        ratiosd=ratiosd,
        ppmunk=ppmunk,
        ratiounk=ratiounk,
        ppmthr=ppmthr,
        pRTNone=pRTNone,
        pRTout=pRTout,
        mzdCS=mzdCS,
        ppmCS=ppmCS,
        CSunk=CSunk,
        evfilt=evfilt,
        ncores=ncores,
    )
    annotations_flat = flattern_annotations(annotations)
    write_func, file_path = output_dataset
    write_func(annotations_flat, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        """Annotation of the dataset base on the MS1 and MS2 information. Prior
    probabilities are based on mass only, while post probabilities are based
    on mass, RT, previous knowledge and isotope patterns."""
    )
    parser.add_argument(
        "--input_dataset_mapped_isotope_patterns",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing the MS1 data. Ideally obtained from map_isotope_patterns",
    )
    parser.add_argument(
        "--input_dataset_MS2",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing the MS2 fragmentation data",
    )
    parser.add_argument(
        "--input_dataset_adducts",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing the information on all the possible adducts given the database. Ideally obtained from compute_all_adducts",
    )
    parser.add_argument(
        "--input_dataset_MS2_DB",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing the MS2 database",
    )
    parser.add_argument(
        "--ppm",
        type=float,
        required=True,
        help="accuracy of the MS instrument used.",
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
        "--mzdCS",
        type=int,
        default=0,
        help="""maximum mz difference allowed when computing cosine similarity
           scores. If one wants to use this parameter instead of ppmCS, this
           must be set to 0. Default 0.""",
    )
    parser.add_argument(
        "--ppmCS",
        type=int,
        default=10,
        help="""maximum ppm allowed when computing cosine similarity scores.
           If one wants to use this parameter instead of mzdCS, this must be
           set to 0. Default 10.""",
    )
    parser.add_argument(
        "--CSunk",
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
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="MS2 annotation file for outputting results.",
    )
    parser.add_argument(
        "--ncores",
        type=int,
        default=None,
        help="number of cores to use for the computation.",
    )
    args = parser.parse_args()
    main(
        args.input_dataset_mapped_isotope_patterns,
        args.input_dataset_MS2,
        args.input_dataset_adducts,
        args.input_dataset_MS2_DB,
        args.ppm,
        args.ratiosd,
        args.ppmunk,
        args.ratiounk,
        args.ppmthr,
        args.pRTNone,
        args.pRTout,
        args.mzdCS,
        args.ppmCS,
        args.CSunk,
        args.evfilt,
        args.output_dataset,
        args.ncores,
    )
