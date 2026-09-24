from ipaPy2 import ipa
from utils import flattern_annotations, GibbsArgumentParser, group_by_peak_id


def main(
    mapped_isotope_patterns,
    annotations_df,
    noits,
    burn,
    delta_add,
    all_out,
    zs,
    zs_out,
    output_dataset,
):
    df = mapped_isotope_patterns

    annotations_df = annotations_df
    annotations_df["post"] = annotations_df["post"].replace("", 0)
    annotations_df = annotations_df.replace("", None)
    annotations = group_by_peak_id(annotations_df)

    if not zs:
        zs = None

    zs = ipa.Gibbs_sampler_add(
        df,
        annotations,
        noits=noits,
        burn=burn,
        delta_add=delta_add,
        all_out=all_out,
        zs=zs,
    )

    annotations_flat = flattern_annotations(annotations)
    write_func, file_path = output_dataset
    write_func(annotations_flat, file_path)

    if all_out:
        write_func, file_path = zs_out
        write_func(zs, file_path)


if __name__ == "__main__":
    parser = GibbsArgumentParser(description="cluster features before IPA pipeline.")
    parser.add_argument(
        "--input_dataset_mapped_isotope_patterns",
        nargs=2,
        action="load_data",
        required=True,
        help=(
            "A dataset containing the MS1 data. Ideally obtained from"
            " map_isotope_patterns"
        ),
    )
    parser.add_argument(
        "--input_dataset_annotations",
        nargs=2,
        action="load_data",
        required=True,
        help="a datset containing the annotations of the features.",
    )

    args = parser.parse_args()
    main(
        args.input_dataset_mapped_isotope_patterns,
        args.input_dataset_annotations,
        args.noits,
        args.burn,
        args.delta_add,
        args.all_out,
        args.zs,
        args.zs_out,
        args.output_dataset,
    )
