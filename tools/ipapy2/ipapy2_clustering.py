import argparse
from ipaPy2 import ipa
from utils import LoadDataAction, StoreOutputAction


def main(input_dataset, Cthr, RTwin, Intmode, output_dataset):
    unclustered_df = input_dataset
    write_func, file_path = output_dataset
    clustered_df = ipa.clusterFeatures(
        unclustered_df, Cthr=Cthr, RTwin=RTwin, Intmode=Intmode
    )
    write_func(clustered_df, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=" Clustering MS1 features based on correlation across samples."
    )
    parser.add_argument(
        "--input_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="The unclustered MS1 intensities file path.",
    )

    parser.add_argument(
        "--Cthr",
        type=float,
        default=0.8,
        help="Minimum correlation allowed in each cluster. Default value 0.8.",
    )

    parser.add_argument(
        "--RTwin",
        type=float,
        default=1,
        help="Maximum difference in RT time between features in the same cluster. Default value 1.",
    )

    parser.add_argument(
        "--Intmode",
        type=str,
        default="max",
        choices=["max", "ave"],
        help="intensity mode. Default 'max' or 'ave'.",
    )

    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="The clustered MS1 intensities file path.",
    )

    args = parser.parse_args()
    main(args.input_dataset, args.Cthr, args.RTwin, args.Intmode, args.output_dataset)
