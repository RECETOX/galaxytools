"""
Command line tool that writes a synchronised peakmap report for a folder of .mzml files.

"""

import argparse
from pathlib import Path

import utils



class ReportHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """
    Help text that only prints a default for the options that actually have one.

    Inputs:
        argparse.ArgumentDefaultsHelpFormatter=parent class that appends
            "(default: ...)" to the help of every option
    outputs:
        none=argparse helper class, its instances render the text of -h
    """

    def _get_help_string(self, action):
        """
        Help string of one option, without a "(default: None)" suffix.

        Inputs:
            action=argparse action whose help text is rendered
        outputs:
            help=text written next to the option in the help of the parser
        """
        if action.default is None:
            return action.help

        return super()._get_help_string(action)



def parse_arguments(argv=None):
    """
    Read the settings of the report from the command line.

    Inputs:
        argv=arguments to parse, None takes them from sys.argv
    outputs:
        arguments=parsed argparse namespace, every option of the parser is an attribute
    """

    parser = argparse.ArgumentParser(
        description=(
            "Plot one 3D peakmap per .mzml file of a folder into a single HTML "
            "report with synchronised rotation and axis ranges."
        ),
        formatter_class=ReportHelpFormatter,
    )

    parser.add_argument(
        "--mzml_folder",
        type=Path,
        required=True,
        help="path to the folder containing the .mzml files",
    )

    parser.add_argument(
        "--rt-min", 
        type=float, 
        required=True, 
        help="lowest retention time to display"
    )
    
    parser.add_argument(
        "--rt-max", 
        type=float, 
        required=True, 
        help="highest retention time to display"
    )
    
    parser.add_argument(
        "--mz-min",
        type=float, 
        required=True, 
        help="lowest m/z to display"
    )
    
    parser.add_argument(
        "--mz-max", 
        type=float, 
        required=True, 
        help="highest m/z to display"
    )
    
    parser.add_argument(
        "--pattern",
        default="*.mzml",
        help="glob that picks the files in the folder, use '*.mzML' on a case sensitive filesystem",
    )

    parser.add_argument(
        "--colour-all",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "colour every peak of the displayed range. With --no-colour-all only the "
            "peaks inside the mz / rt box around --ion-mz and --ion-rt are coloured and "
            "everything else is drawn lightgray."
        ),
    )

    parser.add_argument(
        "--ion-mz", 
        type=float, 
        help="m/z of the ion to colour, needed with --no-colour-all"
    )

    parser.add_argument(
        "--ion-rt",
        type=float,
        help="retention time of the ion to colour in the time unit of the .mzml file, needed with --no-colour-all",
    )

    parser.add_argument(
        "--mz-to-colour-ppm",
        type=float,
        default=utils.MZ_TO_COLOUR_PPM,
        help="half width of the coloured m/z box in ppm of --ion-mz",
    )

    parser.add_argument(
        "--rt-to-colour",
        type=float,
        default=utils.RT_TO_COLOUR,
        help="half width of the coloured retention time box, in the time unit of the .mzml file",
    )

    parser.add_argument(
        "--annotation", 
        default=utils.ANNOTATION, 
        help="name of the coloured region"
    )

    parser.add_argument(
        "--title", 
        help="title of the report page, defaults to '<annotation> in raw data'"
    )
    
    parser.add_argument(
        "--output", 
        type=Path, 
        help="HTML file to write, defaults to <annotation>_peakmaps.html in the current folder"
    )

    parser.add_argument(
        "--colorscale", 
        default=utils.COLORSCALE, 
        help="plotly colorscale of the coloured peaks"
    )
    
    parser.add_argument(
        "--panel-width", 
        type=int, 
        default=utils.panel_width, 
        help="smallest panel width in pixels"
    )
    
    parser.add_argument(
        "--panel-height", 
        type=int, 
        default=utils.panel_height, 
        help="height of every panel in pixels"
    )

    parser.add_argument(
        "--panels-per-row", 
        type=int, 
        default=utils.panels_per_row, 
        help="largest number of panels next to each other"
    )

    parser.add_argument(
        "--max-live-plots",
        type=int,
        default=utils.max_live_plots,
        help="number of plotly graphs the browser may keep alive at once",
    )

    arguments = parser.parse_args(argv)

    if not arguments.mzml_folder.is_dir():
        parser.error(f"{arguments.mzml_folder} is not a folder")

    if arguments.rt_min >= arguments.rt_max:
        parser.error("--rt-min has to be smaller than --rt-max")

    if arguments.mz_min >= arguments.mz_max:
        parser.error("--mz-min has to be smaller than --mz-max")

    if not arguments.colour_all and (arguments.ion_mz is None or arguments.ion_rt is None):
        parser.error("--ion-mz and --ion-rt are required together with --no-colour-all")

    if arguments.title is None:
        arguments.title = f"{arguments.annotation} in raw data"

    if arguments.output is None:
        arguments.output = Path.cwd() / f"{arguments.annotation}_peakmaps.html"

    return arguments



def create_peakmap_report(arguments):
    """
    Load the measurements, label them and write the HTML report.

    Inputs:
        arguments=parsed namespace from parse_arguments() holding the folder, the
            displayed range, what to colour and the look of the report
    outputs:
        report=dict with the keys "output_file" (path of the written HTML file),
            "measurements" (number of panels), "names" (titles of the panels),
            "color_range" (shared log10 intensity range) and "axis_ranges"
            (shared rt / mz / intensity ranges)
    """
    rt_range = (arguments.rt_min, arguments.rt_max)
    mz_range = (arguments.mz_min, arguments.mz_max)

    list_of_mzml_dfs = utils.load_mzml_folder(
        arguments.mzml_folder,
        rt_range,
        mz_range,
        pattern=arguments.pattern,
    )

    # Peaks outside of the coloured box stay lightgray.
    for _, sample_df in list_of_mzml_dfs:
        utils.label_peaks(
            sample_df,
            annotation=arguments.annotation,
            colour_all=arguments.colour_all,
            ion_mz=arguments.ion_mz,
            ion_rt=arguments.ion_rt,
            mz_to_colour_ppm=arguments.mz_to_colour_ppm,
            rt_to_colour=arguments.rt_to_colour,
        )

    # One view, one color scale and one set of axis ranges for every panel.
    panel_ranges = utils.shared_axis_ranges(list_of_mzml_dfs)
    color_rng = utils.shared_color_range(list_of_mzml_dfs)

    peakmap_figures = []
    panel_titles = []
    panel_meta = []

    for name, sample_df in list_of_mzml_dfs:
        peakmap_figures.append(
            utils.build_peakmap_figure(
                sample_df,
                color_range=color_rng,
                panel_ranges=panel_ranges,
                colorscale=arguments.colorscale,
                width=arguments.panel_width,
                height=arguments.panel_height,
            )
        )
        panel_titles.append(str(name))
        panel_meta.append(utils.panel_summary(sample_df))

    output_file = utils.write_synchronized_peakmaps_html(
        peakmap_figures,
        panel_titles,
        output_file=arguments.output,
        panel_meta=panel_meta,
        page_title=arguments.title,
        color_range=color_rng,
        colorscale=arguments.colorscale,
        min_column_width=arguments.panel_width,
        panel_height=arguments.panel_height,
        panels_per_row=arguments.panels_per_row,
        max_live_plots=arguments.max_live_plots,
    )

    return {
        "output_file": output_file,
        "measurements": len(peakmap_figures),
        "names": panel_titles,
        "color_range": color_rng,
        "axis_ranges": panel_ranges,
    }



def main(argv=None):
    """
    Entry point of the command line tool: parse, plot and report what was written.

    Inputs:
        argv=arguments to parse, None takes them from sys.argv
    outputs:
        exit_code=0 when the report was written, 1 when the data could not be plotted
    """
    arguments = parse_arguments(argv)

    try:
        report = create_peakmap_report(arguments)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print("Measurements:", report["measurements"])
    print("Shared color range, log10(intensity + 1):", report["color_range"])
    print("Shared axis ranges:", report["axis_ranges"])
    print("Saved plot to:", report["output_file"])

    return 0



if __name__ == "__main__":
    raise SystemExit(main())
