from ipaPy2 import ipa

from utils import CustomArgumentParser


def main(
    input_dataset_adducts, input_dataset_database, ionisation, output_dataset, ncores
):
    write_func, file_path = output_dataset
    adducts_df = ipa.compute_all_adducts(
        input_dataset_adducts, input_dataset_database, ionisation, ncores
    )

    write_func(adducts_df, file_path)


if __name__ == "__main__":
    parser = CustomArgumentParser(
        description=" Clustering MS1 features based on correlation across samples."
    )
    parser.add_argument(
        "--input_dataset_adducts",
        nargs=2,
        action="load_data",
        required=True,
        help="A dataset containing information on all possible adducts.",
    )
    parser.add_argument(
        "--input_dataset_database",
        nargs=2,
        action="load_data",
        required=True,
        help="The MS1 database.",
    )
    parser.add_argument(
        "--ionisation",
        type=int,
        default=1,
        choices=[1, -1],
        help="Default value 1. positive = 1, negative = -1",
    )
    parser.add_argument(
        "--ncores",
        type=int,
        default=1,
        help="Number of cores to use for parallel processing.",
    )
    args = parser.parse_args()
    main(
        args.input_dataset_adducts,
        args.input_dataset_database,
        args.ionisation,
        args.output_dataset,
        args.ncores,
    )
