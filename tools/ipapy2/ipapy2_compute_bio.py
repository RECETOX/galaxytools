from ipaPy2 import ipa
from utils import CustomArgumentParser, group_by_peak_id


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
        raise ValueError(
            "biochemical_mode must be 'connections' and connection_list must be provided."
        )

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
    parser = CustomArgumentParser(
        description=""" Compute matrix of biochemical connections. Either based on a list of
    possible connections in the form of a list of formulas or based on the
    reactions present in the database."""
    )
    parser.add_argument(
        "--input_dataset_database",
        nargs=2,
        action="load_data",
        required=True,
        help=(
            "a datset containing the database against which the annotationis performed."
        ),
    )
    parser.add_argument(
        "--input_dataset_annotations",
        nargs=2,
        action="load_data",
        help="a datset containing the annotations of the features.",
    )
    parser.add_argument(
        "--biochemical_mode",
        type=str,
        required=True,
        help="""either 'reactions' (connections are computed based on the reactions
          present in the database) or 'connections' (connections are computed
          based on the list of connections provided). Default 'reactions'. """,
    )
    parser.add_argument(
        "--connection_list", type=str, help="intensity mode. Default 'max' or 'ave'."
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
