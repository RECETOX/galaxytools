import argparse
from ipaPy2 import ipa
from utils import LoadDataAction, StoreOutputAction, group_by_peak_id


def main(
    input_dataset_database,
    input_dataset_annotations,
    biochemical_mode,
    connection_list,
    output_dataset,
    ncores,
):
    """
    Compute matrix of biochemical connections. Either based on a list of
    possible connections in the form of a list of formulas or based on the
    reactions present in the database.
    """

    if input_dataset_annotations is not None:
        annotations = group_by_peak_id(input_dataset_annotations)
    else:
        annotations = None

    if biochemical_mode == "connections" and connection_list:
        connections = connection_list
    else:
        connections = [
            "C3H5NO",
            "C6H12N4O",
            "C4H6N2O2",
            "C4H5NO3",
            "C3H5NOS",
            "C6H10N2O3S2",
            "C5H7NO3",
            "C5H8N2O2",
            "C2H3NO",
            "C6H7N3O",
            "C6H11NO",
            "C6H11NO",
            "C6H12N2O",
            "C5H9NOS",
            "C9H9NO",
            "C5H7NO",
            "C3H5NO2",
            "C4H7NO2",
            "C11H10N2O",
            "C9H9NO2",
            "C5H9NO",
            "C4H4O2",
            "C3H5O",
            "C10H12N5O6P",
            "C10H15N2O3S",
            "C10H14N2O2S",
            "CH2ON",
            "C21H34N7O16P3S",
            "C21H33N7O15P3S",
            "C10H15N3O5S",
            "C5H7",
            "C3H2O3",
            "C16H30O",
            "C8H8NO5P",
            "CH3N2O",
            "C5H4N5",
            "C10H11N5O3",
            "C10H13N5O9P2",
            "C10H12N5O6P",
            "C9H13N3O10P2",
            "C9H12N3O7P",
            "C4H4N3O",
            "C10H13N5O10P2",
            "C10H12N5O7P",
            "C5H4N5O",
            "C10H11N5O4",
            "C10H14N2O10P2",
            "C10H12N2O4",
            "C5H5N2O2",
            "C10H13N2O7P",
            "C9H12N2O11P2",
            "C9H11N2O8P",
            "C4H3N2O2",
            "C9H10N2O5",
            "C2H3O2",
            "C2H2O",
            "C2H2",
            "CO2",
            "CHO2",
            "H2O",
            "H3O6P2",
            "C2H4",
            "CO",
            "C2O2",
            "H2",
            "O",
            "P",
            "C2H2O",
            "CH2",
            "HPO3",
            "NH2",
            "PP",
            "NH",
            "SO3",
            "N",
            "C6H10O5",
            "C6H10O6",
            "C5H8O4",
            "C12H20O11",
            "C6H11O8P",
            "C6H8O6",
            "C6H10O5",
            "C18H30O15",
        ]

    Bio = ipa.Compute_Bio(
        input_dataset_database,
        annotations=annotations,
        mode=biochemical_mode,
        connections=connections,
        ncores=ncores,
    )
    write_func, file_path = output_dataset
    write_func(Bio, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=""" Compute matrix of biochemical connections. Either based on a list of
    possible connections in the form of a list of formulas or based on the
    reactions present in the database."""
    )
    parser.add_argument(
        "--input_dataset_database",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="a datset containing the database against which the annotationis performed.",
    )
    parser.add_argument(
        "--input_dataset_annotations",
        nargs=2,
        action=LoadDataAction,
        help="a datset containing the annotations of the features.",
    )
    parser.add_argument(
        "--biochemical_mode",
        type=str,
        required=True,
        help="Default value 1. Maximum difference in RT time between features in the same cluster.",
    )
    parser.add_argument(
        "--connection_list", type=str, help="intensity mode. Default 'max' or 'ave'."
    )
    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="Output file path for the dataframe.",
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
        args.input_dataset_annotations,
        args.biochemical_mode,
        args.connection_list,
        args.output_dataset,
        args.ncores,
    )
