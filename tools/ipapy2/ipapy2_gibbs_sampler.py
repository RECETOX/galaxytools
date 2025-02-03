import argparse


from ipaPy2 import ipa
from utils import (
    flattern_annotations,
    group_by_peak_id,
    LoadDataAction,
    LoadTextAction,
    StoreOutputAction,
)


def main(
    input_dataset_mapped_isotope_patterns,
    input_dataset_annotations,
    integrating_mode,
    input_dataset_bio,
    noits,
    burn,
    delta_bio,
    delta_add,
    all_out,
    zs,
    zs_out,
    output_dataset,
):
    annotations_df = input_dataset_annotations
    annotations_df["post"] = annotations_df["post"].replace("", 0)
    annotations_df = annotations_df.replace("", None)
    annotations = group_by_peak_id(annotations_df)

    if not zs:
        zs = None

    if integrating_mode == "adducts":
        zs = ipa.Gibbs_sampler_add(
            input_dataset_mapped_isotope_patterns,
            annotations,
            noits=noits,
            burn=burn,
            delta_add=delta_add,
            all_out=all_out,
            zs=zs,
        )
    else:
        if args.integrating_mode == "biochemical":
            zs = ipa.Gibbs_sampler_bio(
                input_dataset_mapped_isotope_patterns,
                annotations,
                Bio=input_dataset_bio,
                noits=noits,
                burn=burn,
                delta_bio=delta_bio,
                all_out=all_out,
                zs=zs,
            )
        else:
            zs = ipa.Gibbs_sampler_bio_add(
                input_dataset_mapped_isotope_patterns,
                annotations,
                Bio=input_dataset_bio,
                noits=noits,
                burn=burn,
                delta_bio=delta_bio,
                delta_add=delta_add,
                all_out=all_out,
                zs=zs,
            )

    annotations_flat = flattern_annotations(annotations)
    write_func, file_path = output_dataset
    write_func(annotations_flat, file_path)

    if args.all_out:
        write_func, file_path = zs_out
        write_func(zs, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="cluster features before IPA pipeline."
    )
    parser.add_argument(
        "--input_dataset_mapped_isotope_patterns",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="a dataframe containing the measured intensities across several samples.",
    )
    parser.add_argument(
        "--input_dataset_annotations",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="a datset containing the annotations of the features.",
    )
    parser.add_argument(
        "--integrating_mode",
        type=str,
        required=True,
        choices=["adducts", "biochemical", "biochemical_adducts"],
        help="The mode of integration. Options are 'adducts', 'biochemical', or 'biochemical_adducts'.",
    )
    parser.add_argument(
        "--input_dataset_bio",
        nargs=2,
        action=LoadDataAction,
        type=str,
        help="""dataframe (2 columns), reporting all the possible connections between
         compounds. It uses the unique ids from the database. It could be the
         output of Compute_Bio() or Compute_Bio_Parallel()""",
    )
    parser.add_argument(
        "--noits",
        type=int,
        help="number of iterations if the Gibbs sampler to be run",
    )
    parser.add_argument(
        "--burn",
        type=int,
        help="""number of iterations to be ignored when computing posterior
          probabilities. If None, is set to 10% of total iterations""",
    )
    parser.add_argument(
        "--delta_bio",
        type=float,
        help="""parameter used when computing the conditional priors. The
               parameter must be positive. The smaller the parameter the more
               weight the adducts connections have on the posterior
               probabilities. Default 1.""",
    )
    parser.add_argument(
        "--delta_add",
        type=float,
        help=""" parameter used when computing the conditional priors. The
               parameter must be positive. The smaller the parameter the more
               weight the adducts connections have on the posterior
               probabilities. Default 1.""",
    )
    parser.add_argument(
        "--all_out",
        type=str,
        help="""logical value. If true the list of assignments found in each
            iteration is returned by the function. Default False.""",
    )
    parser.add_argument(
        "--zs",
        nargs=2,
        action=LoadTextAction,
        help="""a txt file containing the list of assignments computed in a previous run of the Gibbs sampler.
        Optional, default None.""",
    )
    parser.add_argument(
        "--zs_out",
        nargs=2,
        action=StoreOutputAction,
        help="file to save the list of assignments computed in the current run of the Gibbs sampler.",
    )
    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="A file path for the output results from Gibbs Add.",
    )
    args = parser.parse_args()
    main(
        args.input_dataset_mapped_isotope_patterns,
        args.input_dataset_annotations,
        args.integrating_mode,
        args.input_dataset_bio,
        args.noits,
        args.burn,
        args.delta_bio,
        args.delta_add,
        args.all_out,
        args.zs,
        args.zs_out,
        args.output_dataset,
    )
