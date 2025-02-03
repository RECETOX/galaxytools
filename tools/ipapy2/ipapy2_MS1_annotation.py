import argparse


from ipaPy2 import ipa
from utils import LoadDataAction, StoreOutputAction, flattern_annotations


def main(
    input_dataset_database,
    input_dataset_adduct,
    ppm,
    ratiosd,
    ppmunk,
    ratiounk,
    ppmthr,
    pRTNone,
    pRTout,
    output_dataset,
    ncores,
):
    write_func, file_path = output_dataset
    ncores = ncores if ncores else 1
    ppmunk = ppmunk if ppmunk else ppm
    ppmthr = ppmthr if ppmthr else 2 * ppm

    annotations = ipa.MS1annotation(
        input_dataset_database,
        input_dataset_adduct,
        ppm=ppm,
        ratiosd=ratiosd,
        ppmunk=ppmunk,
        ratiounk=ratiounk,
        ppmthr=ppmthr,
        pRTNone=pRTNone,
        pRTout=pRTout,
        ncores=ncores,
    )
    annotations_flat = flattern_annotations(annotations)
    write_func(annotations_flat, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        """
    Annotation of the dataset based on the MS1 information. Prior probabilities
        are based on mass only, while post probabilities are based on mass, RT,
        previous knowledge and isotope patterns.
    """
    )
    parser.add_argument(
        "--input_dataset_database",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing the MS1 data. Ideally obtained from map_isotope_patterns",
    )
    parser.add_argument(
        "--input_dataset_adducts",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="A dataset containing information on all possible adducts.",
    )
    parser.add_argument(
        "--ppm",
        type=float,
        required=True,
        default=100,
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
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="MS1 annotated data",
    )
    parser.add_argument(
        "--ncores",
        type=int,
        default=None,
        help="number of cores to use for the computation.",
    )
    args = parser.parse_args()
    main(
        args.input_dataset_database,
        args.input_dataset_adducts,
        args.ppm,
        args.ratiosd,
        args.ppmunk,
        args.ratiounk,
        args.ppmthr,
        args.pRTNone,
        args.pRTout,
        args.output_dataset,
        args.ncores,
    )
