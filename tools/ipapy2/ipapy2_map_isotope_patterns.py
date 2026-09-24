from ipaPy2 import ipa
from utils import CustomArgumentParser


def main(input_dataset, isoDiff, ppm, ionisation, isotope_ratio, output_dataset):
    clustered_df = input_dataset
    ipa.map_isotope_patterns(
        clustered_df,
        isoDiff=isoDiff,
        ppm=ppm,
        ionisation=ionisation,
        MinIsoRatio=isotope_ratio,
    )
    write_func, file_path = output_dataset
    write_func(clustered_df, file_path)


if __name__ == "__main__":
    parser = CustomArgumentParser(description="mapping isotope patterns in MS1 data.")
    parser.add_argument(
        "--input_dataset",
        nargs=2,
        action="load_data",
        required=True,
        help="A dataset containing clustered MS1 intensities.",
    )
    parser.add_argument(
        "--isoDiff",
        type=float,
        default=1,
        help=(
            "Default value 1. Difference between isotopes of charge 1, does            "
            "  not need to be exact"
        ),
    )
    parser.add_argument(
        "--ppm",
        type=float,
        default=100,
        help=(
            "Default value 100. Maximum ppm value allowed between 2 isotopes.          "
            "  It is very high on purpose"
        ),
    )
    parser.add_argument(
        "--ionisation",
        type=int,
        default=1,
        choices=[1, -1],
        help="Default value 1. positive = 1, negative = -1",
    )
    parser.add_argument(
        "--isotope_ratio",
        type=float,
        default=1,
        help=(
            "mininum intensity ratio expressed (Default value 1%). Only               "
            " isotopes with intensity higher than MinIsoRatio% of the main isotope     "
            "           are considered."
        ),
    )
    args = parser.parse_args()
    main(
        args.input_dataset,
        args.isoDiff,
        args.ppm,
        args.ionisation,
        args.isotope_ratio,
        args.output_dataset,
    )
