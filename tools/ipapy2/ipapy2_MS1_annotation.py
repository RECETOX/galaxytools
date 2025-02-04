import argparse

from ipaPy2 import ipa

from utils import MSArgumentParser, flattern_annotations


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
    parser = MSArgumentParser(
        """
    Annotation of the dataset based on the MS1 information. Prior probabilities
        are based on mass only, while post probabilities are based on mass, RT,
        previous knowledge and isotope patterns.
    """
    )
    parser.add_argument(
        "--input_dataset_database",
        nargs=2,
        action="load_data",
        required=True,
        help="A dataset containing the MS1 data. Ideally obtained from map_isotope_patterns",
    )
    parser.add_argument(
        "--input_dataset_adducts",
        nargs=2,
        action="load_data",
        required=True,
        help="A dataset containing information on all possible adducts.",
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
