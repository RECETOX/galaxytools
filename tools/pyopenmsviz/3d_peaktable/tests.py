"""Tests for the peakmap report of utils.py and the command line tool main.py.

The tests that read raw data run on the small dummy files in test-data, which are
subsamples of a real measurement (see make_test_data.py):

    python make_test_data.py
    pytest tests.py -v
"""

import json
import math
import re
from pathlib import Path

import pandas as pd
import pytest

import main
import utils


HERE = Path(__file__).resolve().parent
TEST_DATA = HERE / "test-data"

# window and ion of the report that was built in the notebook
RT_RANGE = (455.0, 462.0)
MZ_RANGE = (324.0, 333.0)
ION_MZ = 329.3203
ION_RT = 458.6873

# half widths of the coloured box, the same values the report uses
MZ_TO_COLOUR_PPM = 5.0
RT_TO_COLOUR = 2.0

# one m/z offset that lands inside and one that lands outside of the coloured box
INSIDE_MZ_OFFSET = ION_MZ * MZ_TO_COLOUR_PPM * 1e-6 / 2
OUTSIDE_MZ_OFFSET = ION_MZ * MZ_TO_COLOUR_PPM * 1e-6 * 10



@pytest.fixture(scope="session")
def mzml_folder():
    """
    Folder with the dummy .mzml files that the raw data tests read.

    Inputs:
        none=pytest fixture without arguments
    outputs:
        mzml_folder=path to test-data, tests using it are skipped while the dummy
            files are missing
    """
    if not list(TEST_DATA.glob("*.mzml")):
        pytest.skip(f"no dummy files in {TEST_DATA}, run 'python make_test_data.py'")

    return TEST_DATA



@pytest.fixture(scope="session")
def labelled_measurements(mzml_folder):
    """
    Dummy measurements of the peak window with the ion already labelled.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        list_of_mzml_dfs=list of (file stem, DataFrame) tuples sorted by name, the
            blank file is dropped because it has no peak in this window
    """
    list_of_mzml_dfs = utils.load_mzml_folder(mzml_folder, RT_RANGE, MZ_RANGE)

    for _, sample_df in list_of_mzml_dfs:
        utils.label_peaks(
            sample_df,
            colour_all=False,
            ion_mz=ION_MZ,
            ion_rt=ION_RT,
            mz_to_colour_ppm=MZ_TO_COLOUR_PPM,
            rt_to_colour=RT_TO_COLOUR,
        )

    return list_of_mzml_dfs



def sample_frame():
    """
    Tiny measurement with peaks on both sides of every border of the coloured box.

    Inputs:
        none=this frame is fixed, it has no arguments
    outputs:
        df=DataFrame with three peaks inside and two peaks outside of the box
            around (ION_MZ, ION_RT), intensities between 10 and 1e5
    """
    return pd.DataFrame(
        {
            "rt": [ION_RT, ION_RT + 1.0, ION_RT - RT_TO_COLOUR, ION_RT + RT_TO_COLOUR + 1.0, ION_RT],
            "mz": [ION_MZ, ION_MZ + INSIDE_MZ_OFFSET, ION_MZ, ION_MZ, ION_MZ + OUTSIDE_MZ_OFFSET],
            "intensity": [1e5, 1e3, 1e2, 1e1, 1e4],
        }
    )



def labelled_frame():
    """
    sample_frame with the default ion box applied to it.

    Inputs:
        none=uses sample_frame and the ion constants of this module
    outputs:
        df=DataFrame with the column "label", three rows are annotated and two stay unknown
    """
    return utils.label_peaks(
        sample_frame(),
        annotation="target",
        colour_all=False,
        ion_mz=ION_MZ,
        ion_rt=ION_RT,
        mz_to_colour_ppm=MZ_TO_COLOUR_PPM,
        rt_to_colour=RT_TO_COLOUR,
    )



def two_measurements():
    """
    Two labelled measurements that differ in size and in intensity.

    Inputs:
        none=this pair is fixed, it has no arguments
    outputs:
        list_of_mzml_dfs=list of two (name, DataFrame) tuples, the second one adds
            a dim annotated peak and one peak that stays unknown
    """
    first = pd.DataFrame(
        {
            "rt": [1.0, 2.0],
            "mz": [100.0, 200.0],
            "intensity": [1e3, 1e7],
            "label": ["target", "target"],
        }
    )
    second = pd.DataFrame(
        {
            "rt": [1.0, 2.0, 3.0],
            "mz": [100.0, 200.0, 300.0],
            "intensity": [1e1, 1e5, 1e2],
            "label": ["target", "target", utils.UNKNOWN_LABEL],
        }
    )

    return [("first", first), ("second", second)]



def binned_frame():
    """
    Measurement with more peaks than the 50 x 50 bins of pyopenms_viz, so every
    panel built from it is aggregated.

    The tall peak (150 million) lies outside the ion box of the constants of
    this module and shares its rt / mz bin with the two dim peaks inside the
    box: binning averages it with them when everything is coloured, but leaves
    it alone when only the ion box is coloured.

    Inputs:
        none=this frame is fixed, it has no arguments
    outputs:
        df=DataFrame with 2603 peaks whose tallest bin average is lower than
            its tallest peak
    """
    n_filler = 2600

    return pd.DataFrame(
        {
            "rt": [ION_RT, ION_RT, ION_RT + 0.01]
            + [457.0 + (i % 130) * 0.02 for i in range(n_filler)],
            "mz": [ION_MZ - 0.05, ION_MZ, ION_MZ]
            + [324.0 + (i // 130) * 0.002 for i in range(n_filler)],
            "intensity": [1.5e8, 100.0, 100.0] + [1000.0] * n_filler,
        }
    )



def peakmap_config(html):
    """
    Read the peakmapConfig JSON that a written report embeds.

    Inputs:
        html=contents of a report written by write_synchronized_peakmaps_html
    outputs:
        config=dict the panels are built from, with the keys figures, camera,
            defaultAxes, maxLive and the two sync switches
    """
    marker = "window.peakmapConfig = "
    start = html.index(marker) + len(marker)
    end = html.index(";</script>", start)

    return json.loads(html[start:end])



def app_script(html):
    """
    Script of the report itself, without the bundled plotly in front of it.

    Inputs:
        html=contents of a report written by write_synchronized_peakmaps_html
    outputs:
        script=text of the last script tag, the one that drives the panels
    """
    return html.rsplit("<script>", 1)[1].split("</script>", 1)[0]



def trace_names(config):
    """
    Names of every trace of every panel of a written report.

    Inputs:
        config=dict returned by peakmap_config
    outputs:
        names=set of the label of each trace, which is the legend entry in the report
    """
    return {trace["name"] for panel in config["figures"] for trace in panel["data"]}



# ---------------------------------------------------------------- reading raw data
def test_load_mzml_df_keeps_the_requested_range(mzml_folder):
    """
    Only the peaks inside the requested retention time and m/z window are read.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        none=the test only asserts
    """
    df = utils.load_mzml_df(mzml_folder / "dummy_peak_a.mzml", (457.0, 460.0), (325.0, 332.0))

    assert not df.empty
    assert {"rt", "mz", "intensity"} <= set(df.columns)
    assert df["rt"].between(457.0, 460.0).all()
    assert df["mz"].between(325.0, 332.0).all()



def test_load_mzml_df_finds_the_ion_of_the_tests(mzml_folder):
    """
    The subsampled file still holds the ion that the tests colour.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        none=the test only asserts
    """
    df = utils.load_mzml_df(mzml_folder / "dummy_peak_a.mzml", RT_RANGE, MZ_RANGE)
    in_window = (df["mz"] - ION_MZ).abs() <= ION_MZ * MZ_TO_COLOUR_PPM * 1e-6

    assert df["intensity"].max() > 0
    assert (df.loc[in_window, "intensity"].max()) > 0



def test_load_mzml_folder_returns_every_file(mzml_folder):
    """
    Every .mzml file of the folder becomes one panel, sorted by name.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        none=the test only asserts
    """
    list_of_mzml_dfs = utils.load_mzml_folder(mzml_folder, (100.0, 462.0), MZ_RANGE)
    names = [name for name, _ in list_of_mzml_dfs]

    assert names == sorted(names)
    assert names == ["dummy_blank", "dummy_peak_a", "dummy_peak_b"]



def test_load_mzml_folder_uses_the_glob_pattern(mzml_folder):
    """
    The pattern picks single files out of the folder.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        none=the test only asserts
    """
    list_of_mzml_dfs = utils.load_mzml_folder(
        mzml_folder, RT_RANGE, MZ_RANGE, pattern="dummy_peak_a.mzml"
    )

    assert [name for name, _ in list_of_mzml_dfs] == ["dummy_peak_a"]



def test_load_mzml_folder_drops_files_without_peaks(mzml_folder, capsys):
    """
    A file with no peak in the displayed range is skipped and reported.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
        capsys=pytest fixture that captures what is printed
    outputs:
        none=the test only asserts
    """
    list_of_mzml_dfs = utils.load_mzml_folder(mzml_folder, RT_RANGE, MZ_RANGE)

    assert [name for name, _ in list_of_mzml_dfs] == ["dummy_peak_a", "dummy_peak_b"]
    assert "dummy_blank.mzml" in capsys.readouterr().out



def test_load_mzml_folder_needs_files(tmp_path):
    """
    An empty folder is an error instead of an empty report.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    with pytest.raises(ValueError, match="no files matching"):
        utils.load_mzml_folder(tmp_path, RT_RANGE, MZ_RANGE)



# ---------------------------------------------------------------- what gets coloured
def test_colour_window_uses_ppm_for_mz_and_absolute_time_for_rt():
    """
    The box is symmetric around the ion, in ppm for m/z and in time units for rt.

    Inputs:
        none=uses the fixed ion 200 at retention time 50
    outputs:
        none=the test only asserts
    """
    window = utils.colour_window(200.0, 50.0, mz_to_colour_ppm=10.0, rt_to_colour=3.0)

    assert window["mz_min"] == pytest.approx(200.0 - 200.0 * 10e-6)
    assert window["mz_max"] == pytest.approx(200.0 + 200.0 * 10e-6)
    assert window["rt_min"] == pytest.approx(47.0)
    assert window["rt_max"] == pytest.approx(53.0)



def test_label_peaks_colours_the_whole_range_by_default():
    """
    Without arguments every displayed peak is labelled with the annotation.

    Inputs:
        none=uses sample_frame
    outputs:
        none=the test only asserts
    """
    df = utils.label_peaks(sample_frame(), annotation="target")

    assert (df["label"] == "target").all()



def test_label_peaks_colours_only_the_ion_box():
    """
    With colour_all=False only the peaks inside the box are annotated, the border is included.

    Inputs:
        none=uses labelled_frame
    outputs:
        none=the test only asserts
    """
    df = labelled_frame()

    assert (df.loc[[0, 1, 2], "label"] == "target").all()
    assert (df.loc[[3, 4], "label"] == utils.UNKNOWN_LABEL).all()



def test_label_peaks_needs_the_ion_when_it_should_not_colour_everything():
    """
    Selecting a range without saying which ion to select is an error.

    Inputs:
        none=uses sample_frame
    outputs:
        none=the test only asserts
    """
    with pytest.raises(ValueError, match="ion_mz and ion_rt"):
        utils.label_peaks(sample_frame(), colour_all=False)



def test_label_peaks_finds_the_ion_in_real_data(labelled_measurements):
    """
    The ion is found in both peak files and more often in the wider window.

    Inputs:
        labelled_measurements=fixture with the labelled dummy measurements
    outputs:
        none=the test only asserts
    """
    annotated = [int((df["label"] != utils.UNKNOWN_LABEL).sum()) for _, df in labelled_measurements]

    assert all(count > 0 for count in annotated)
    assert annotated[1] > annotated[0]



def test_label_peaks_colours_every_peak_of_real_data(mzml_folder):
    """
    colour_all=True leaves no grey peak behind in a real measurement.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
    outputs:
        none=the test only asserts
    """
    df = utils.load_mzml_df(mzml_folder / "dummy_peak_a.mzml", RT_RANGE, MZ_RANGE)
    utils.label_peaks(df, annotation="target", colour_all=True)

    assert set(df["label"]) == {"target"}



def test_label_peaks_labels_every_file_of_a_report(labelled_measurements):
    """
    Every measurement of a report carries the label column.

    Inputs:
        labelled_measurements=fixture with the labelled dummy measurements
    outputs:
        none=the test only asserts
    """
    for _, sample_df in labelled_measurements:
        assert "label" in sample_df.columns
        assert sample_df["label"].notna().all()



def test_panel_summary_counts_peaks_and_annotation():
    """
    The caption of a panel reports how many peaks are shown and coloured.

    Inputs:
        none=uses labelled_frame
    outputs:
        none=the test only asserts
    """
    assert utils.panel_summary(labelled_frame()) == "5 peaks, 3 annotated"



# ---------------------------------------------------------------- shared ranges
def test_shared_color_range_spans_every_measurement():
    """
    The color scale covers the dimmest and the brightest annotated peak of all files.

    Inputs:
        none=uses two_measurements
    outputs:
        none=the test only asserts
    """
    cmin, cmax = utils.shared_color_range(two_measurements())

    assert cmin == pytest.approx(math.log10(10 + 1))
    assert cmax == pytest.approx(math.log10(1e7 + 1))



def test_shared_color_range_ignores_unknown_peaks():
    """
    Grey peaks do not move the color scale.

    Inputs:
        none=uses two_measurements
    outputs:
        none=the test only asserts
    """
    annotated = two_measurements()[0][1]
    extra_unknown = pd.DataFrame(
        {"rt": [3.0], "mz": [300.0], "intensity": [1e-9], "label": [utils.UNKNOWN_LABEL]}
    )
    with_unknown = pd.concat([annotated, extra_unknown], ignore_index=True)

    cmin_annotated, cmax_annotated = utils.shared_color_range([("a", annotated)])
    cmin_mixed, cmax_mixed = utils.shared_color_range([("b", with_unknown)])

    assert cmin_annotated == pytest.approx(cmin_mixed)
    assert cmax_annotated == pytest.approx(cmax_mixed)



def test_shared_color_range_needs_something_to_colour():
    """
    A report without a single annotated peak is an error.

    Inputs:
        none=uses a frame whose only peak stays unknown
    outputs:
        none=the test only asserts
    """
    only_unknown = two_measurements()[1][1]

    with pytest.raises(ValueError, match="No annotated peaks"):
        utils.shared_color_range([("only", only_unknown[only_unknown["label"] == utils.UNKNOWN_LABEL])])



def test_shared_color_range_is_never_zero_width():
    """
    Identical intensities still give a color scale that the gradient can span.

    Inputs:
        none=uses a single peak measurement
    outputs:
        none=the test only asserts
    """
    flat = pd.DataFrame({"rt": [1.0], "mz": [100.0], "intensity": [1000.0], "label": ["target"]})
    cmin, cmax = utils.shared_color_range([("flat", flat)])

    assert cmax == pytest.approx(cmin + 1)



def test_shared_axis_ranges_cover_every_measurement_and_start_at_zero():
    """
    rt, mz and intensity ranges are the union of all measurements.

    Inputs:
        none=uses two_measurements
    outputs:
        none=the test only asserts
    """
    ranges = utils.shared_axis_ranges(two_measurements())

    assert ranges["rt"] == [1.0, 3.0]
    assert ranges["mz"] == [100.0, 300.0]
    assert ranges["intensity"] == [0.0, pytest.approx(1e7)]



def test_shared_axis_ranges_of_real_data_hold_the_ion(labelled_measurements):
    """
    The shared window still contains the ion that is being coloured.

    Inputs:
        labelled_measurements=fixture with the labelled dummy measurements
    outputs:
        none=the test only asserts
    """
    ranges = utils.shared_axis_ranges(labelled_measurements)

    assert ranges["mz"][0] <= ION_MZ <= ranges["mz"][1]
    assert ranges["rt"][0] <= ION_RT <= ranges["rt"][1]
    assert ranges["intensity"][0] == 0.0



# ---------------------------------------------------------------- colors
def test_stem_colors_has_one_color_per_coordinate():
    """
    Stems get the color of their peak, separators get the bottom of the scale.

    Inputs:
        none=uses a trace of two stems
    outputs:
        none=the test only asserts
    """
    z_values = [0.0, 1e3, None, 0.0, 1e7, None]
    colors = utils.stem_colors(z_values, cmin=1.0)

    assert len(colors) == len(z_values)
    assert colors[2] == 1.0
    # the base of a stem is drawn in the color of its own peak
    assert colors[0] == colors[1] == pytest.approx(math.log10(1e3 + 1))
    assert colors[3] == colors[4] == pytest.approx(math.log10(1e7 + 1))



def test_stem_colors_of_an_empty_trace_is_empty():
    """
    A trace without coordinates gets no colors.

    Inputs:
        none=uses an empty list of coordinates
    outputs:
        none=the test only asserts
    """
    assert utils.stem_colors([], cmin=0.0) == []



def test_report_color_bar_samples_the_colorscale(tmp_path):
    """
    The color bar of the header is built from evenly spaced colors of the scale.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figure = utils.build_peakmap_figure(labelled_frame(), color_range=(1.0, 6.0), panel_ranges=None)

    utils.write_synchronized_peakmaps_html(
        [figure],
        ["run"],
        output_file=tmp_path / "report.html",
        color_range=(1.0, 6.0),
        steps=5,
    )
    gradient = re.search(
        r'background: linear-gradient\(to right, (.*?)"></span>',
        (tmp_path / "report.html").read_text(encoding="utf8"),
    )

    assert gradient, "the header does not hold a color bar gradient"
    # sample_colorscale() is called by write_synchronized_peakmaps_html, five
    # requests of the scale have to come back as five colors of the gradient
    colors = re.findall(r"rgba?\([^)]*\)", gradient.group(1))
    assert len(colors) == 5
    assert all(color.startswith("rgb(") for color in colors)



def test_color_scale_ticks_run_from_cmin_to_cmax():
    """
    The labels of the color bar are spread from its first to its last value.

    Inputs:
        none=uses three ticks between 2 and 8
    outputs:
        none=the test only asserts
    """
    ticks = utils.color_scale_ticks(2.0, 8.0, ticks=3)

    assert [tick["position"] for tick in ticks] == [0.0, 50.0, 100.0]
    assert [tick["value"] for tick in ticks] == [2.0, 5.0, 8.0]



# ---------------------------------------------------------------- panels
def test_build_peakmap_figure_has_one_trace_per_label():
    """
    Annotated and unknown peaks end up in separate traces.

    Inputs:
        none=uses labelled_frame
    outputs:
        none=the test only asserts
    """
    figure = utils.build_peakmap_figure(labelled_frame(), color_range=(1.0, 6.0), panel_ranges=None)

    assert {trace.name for trace in figure.data} == {"target", utils.UNKNOWN_LABEL}



def test_build_peakmap_figure_draws_unknown_peaks_grey():
    """
    Unknown peaks are flat lightgray, annotated ones use the shared color scale.

    Inputs:
        none=uses labelled_frame and the Viridis scale
    outputs:
        none=the test only asserts
    """
    figure = utils.build_peakmap_figure(
        labelled_frame(), color_range=(1.0, 6.0), panel_ranges=None, colorscale="Viridis"
    )

    for trace in figure.data:
        if trace.name == utils.UNKNOWN_LABEL:
            assert trace.line.color == "lightgray"
        else:
            assert trace.line.cmin == 1.0
            assert trace.line.cmax == 6.0
            # plotly expands a named scale into its stops, the first one of Viridis
            assert str(trace.line.colorscale[0][1]).lower() == "#440154"
            assert trace.line.showscale is False
            assert len(trace.line.color) == len(trace.z)



def test_build_peakmap_figure_shares_camera_and_ranges():
    """
    Every panel starts with the same camera and the same axis ranges.

    Inputs:
        none=uses labelled_frame and fixed ranges
    outputs:
        none=the test only asserts
    """
    panel_ranges = {"rt": [1.0, 2.0], "mz": [100.0, 300.0], "intensity": [0.0, 1e5]}
    figure = utils.build_peakmap_figure(
        labelled_frame(), color_range=(1.0, 6.0), panel_ranges=panel_ranges
    )
    scene = figure.to_plotly_json()["layout"]["scene"]

    assert scene["camera"]["eye"] == utils.default_camera["eye"]
    assert list(scene["xaxis"]["range"]) == panel_ranges["rt"]
    assert list(scene["yaxis"]["range"]) == panel_ranges["mz"]
    assert list(scene["zaxis"]["range"]) == panel_ranges["intensity"]



# ---------------------------------------------------------------- drawn ranges
def test_intensity_axis_follows_the_drawn_bars():
    """
    The z axis is scaled to the tallest bar that is drawn, not to the data.

    Binning averages the tall peak with the dim peaks of its bin when
    everything is coloured, so the tallest bar is lower than the tallest peak
    and the axis has to follow the bar.

    Inputs:
        none=uses binned_frame
    outputs:
        none=the test only asserts
    """
    panel_ranges = utils.shared_axis_ranges([("binned", binned_frame())])

    for colour_all, tallest_bar in ((True, (1.5e8 + 100.0 + 100.0) / 3), (False, 1.5e8)):
        df = binned_frame()
        utils.label_peaks(
            df,
            colour_all=colour_all,
            ion_mz=ION_MZ,
            ion_rt=ION_RT,
            mz_to_colour_ppm=MZ_TO_COLOUR_PPM,
            rt_to_colour=RT_TO_COLOUR,
        )
        figure = utils.build_peakmap_figure(df, color_range=(0.0, 9.0), panel_ranges=panel_ranges)

        z_max = utils.apply_shared_intensity_range([figure], utils.drawn_intensity_max([figure]))
        scene = figure.to_plotly_json()["layout"]["scene"]

        assert z_max == pytest.approx(tallest_bar)
        assert scene["zaxis"]["range"] == pytest.approx([0.0, tallest_bar])



def test_color_bar_spans_the_drawn_stems():
    """
    The color scale endpoints come from the stems that are actually drawn.

    Binning averages the peaks of every cell separately for the coloured and
    the grey stems, so the drawn colored stems decide where the scale starts
    and ends, and the grey trace keeps its flat lightgray.

    Inputs:
        none=uses binned_frame
    outputs:
        none=the test only asserts
    """
    tall_bin_mean = (1.5e8 + 100.0 + 100.0) / 3

    for colour_all, drawn in (
        (True, (math.log10(1000.0 + 1), math.log10(tall_bin_mean + 1))),
        (False, (math.log10(100.0 + 1), math.log10(100.0 + 1) + 1)),
    ):
        df = binned_frame()
        utils.label_peaks(
            df,
            colour_all=colour_all,
            ion_mz=ION_MZ,
            ion_rt=ION_RT,
            mz_to_colour_ppm=MZ_TO_COLOUR_PPM,
            rt_to_colour=RT_TO_COLOUR,
        )
        figure = utils.build_peakmap_figure(df, color_range=(0.0, 9.0), panel_ranges=None)

        assert utils.drawn_color_range([figure]) == pytest.approx(drawn)

        utils.apply_shared_color_range([figure], drawn)

        for trace in figure.data:
            if trace.name == utils.UNKNOWN_LABEL:
                assert trace.line.color == "lightgray"
            else:
                assert trace.line.cmin == pytest.approx(drawn[0])
                assert trace.line.cmax == pytest.approx(drawn[1])



# ---------------------------------------------------------------- report
def test_write_report_embeds_every_panel(tmp_path):
    """
    One self contained HTML file holds all panels, their captions and the title.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figures = [
        utils.build_peakmap_figure(df, color_range=(1.0, 6.0), panel_ranges=None)
        for _, df in two_measurements()
    ]
    output_file = tmp_path / "report.html"

    written = utils.write_synchronized_peakmaps_html(
        figures,
        ["first", "second"],
        output_file=output_file,
        panel_meta=["2 peaks", "3 peaks"],
        page_title="Test report",
        color_range=(1.0, 6.0),
    )
    html = written.read_text(encoding="utf8")

    assert written == output_file and output_file.is_file()
    assert html.count('class="panel"') == 2
    assert "first" in html and "second" in html
    assert "2 peaks" in html and "3 peaks" in html
    assert "<title>Test report</title>" in html
    assert "log10(intensity + 1)" in html
    assert "linear-gradient(to right," in html
    assert html.count('class="cb-tick"') == utils.color_bar_ticks
    # plotly is bundled so that the file works offline
    assert "Plotly" in html and len(html) > 1e6



def test_write_report_config_carries_the_shared_view(tmp_path):
    """
    The embedded config holds one payload per panel plus the shared camera and axes.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figures = [
        utils.build_peakmap_figure(df, color_range=(1.0, 6.0), panel_ranges=None)
        for _, df in two_measurements()
    ]

    utils.write_synchronized_peakmaps_html(figures, ["first", "second"], output_file=tmp_path / "report.html")
    config = peakmap_config((tmp_path / "report.html").read_text(encoding="utf8"))

    assert len(config["figures"]) == 2
    assert config["syncRotation"] is True and config["syncAxes"] is True
    assert config["camera"]["eye"] == utils.default_camera["eye"]
    assert set(config["defaultAxes"]) == {"xaxis", "yaxis", "zaxis"}
    # the width of a panel comes from the grid, not from the figure
    assert "width" not in config["figures"][0]["layout"]



def test_write_report_lives_inside_the_webgl_budget(tmp_path):
    """
    The script is told how many graphs it may keep, and that stays under the
    number of webgl contexts a browser is willing to hold.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figures = [
        utils.build_peakmap_figure(df, color_range=(1.0, 6.0), panel_ranges=None)
        for _, df in two_measurements()
    ]

    utils.write_synchronized_peakmaps_html(
        figures, ["first", "second"], output_file=tmp_path / "report.html", max_live_plots=4
    )
    config = peakmap_config((tmp_path / "report.html").read_text(encoding="utf8"))

    assert config["maxLive"] == 4
    # a chromium page keeps about 16 contexts, the budget has to stay below that
    assert 0 < utils.max_live_plots < 16
    assert config["preload"] == utils.preload_pixels



def test_write_report_gives_webgl_contexts_back(tmp_path):
    """
    Purging a panel hands its context back and a lost context does not start the
    recovery loop of plotly.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figure = utils.build_peakmap_figure(labelled_frame(), color_range=(1.0, 6.0), panel_ranges=None)

    utils.write_synchronized_peakmaps_html([figure], ["run"], output_file=tmp_path / "report.html")
    script = app_script((tmp_path / "report.html").read_text(encoding="utf8"))
    destroy = script[script.index("function destroy") : script.index("function lostContext")]

    # WEBGL_lose_context is what Plotly.purge() forgets, and plotly_webglcontextlost
    # is the event plotly would otherwise answer by asking for a new context
    assert "WEBGL_lose_context" in script
    assert "plotly_webglcontextlost" in script
    # purge first so that plotly is off the canvas, then hand the contexts back
    assert destroy.index("Plotly.purge(gd)") < destroy.index("releaseContext(contexts)")
    # a panel that is already gone must not lower the budget a second time
    assert 'if (live.indexOf(index) === -1) return;' in script
    # one graph is built per frame, the panels that came into view queue up
    assert "buildNext()" in script



def test_write_report_escapes_names_but_not_the_script(tmp_path):
    """
    A panel name is escaped like any other text, the report script is not.

    Inputs:
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    figure = utils.build_peakmap_figure(labelled_frame(), color_range=(1.0, 6.0), panel_ranges=None)

    utils.write_synchronized_peakmaps_html(
        [figure], ["run & <2>"], output_file=tmp_path / "report.html", page_title="A & B"
    )
    html = (tmp_path / "report.html").read_text(encoding="utf8")

    assert 'data-name="run &amp; &lt;2&gt;"' in html
    assert "<title>A &amp; B</title>" in html
    # the synchronisation script keeps its plain javascript comparison operators
    assert "i < live.length" in html
    assert "window.peakmapConfig" in html



def test_write_report_needs_one_title_per_figure():
    """
    A panel without a title is an error.

    Inputs:
        none=uses one title and no figure
    outputs:
        none=the test only asserts
    """
    with pytest.raises(ValueError, match="same length"):
        utils.write_synchronized_peakmaps_html([], ["first"], output_file="report.html")



# ---------------------------------------------------------------- command line tool
def test_parse_arguments_colours_everything_by_default():
    """
    Without the flag the whole displayed range is coloured and no ion is needed.

    Inputs:
        none=uses a fixed argument list
    outputs:
        none=the test only asserts
    """
    arguments = main.parse_arguments(
        [
            "--mzml_folder", str(HERE),
            "--rt-min", "457", "--rt-max", "460",
            "--mz-min", "325", "--mz-max", "332",
        ]
    )

    assert arguments.mzml_folder == HERE
    assert arguments.colour_all is True
    assert arguments.annotation == utils.ANNOTATION
    assert (arguments.mz_to_colour_ppm, arguments.rt_to_colour) == (utils.MZ_TO_COLOUR_PPM, utils.RT_TO_COLOUR)



def test_parse_arguments_accepts_a_selected_range_to_colour():
    """
    --no-colour-all turns the ion box on and its half widths are read from the command line.

    Inputs:
        none=uses a fixed argument list
    outputs:
        none=the test only asserts
    """
    arguments = main.parse_arguments(
        [
            "--mzml_folder", str(HERE),
            "--rt-min", "457", "--rt-max", "460",
            "--mz-min", "325", "--mz-max", "332",
            "--no-colour-all",
            "--ion-mz", "329.3203", "--ion-rt", "458.6873",
            "--mz-to-colour-ppm", "3", "--rt-to-colour", "1",
        ]
    )

    assert arguments.colour_all is False
    assert arguments.ion_mz == pytest.approx(329.3203)
    assert arguments.ion_rt == pytest.approx(458.6873)
    assert (arguments.mz_to_colour_ppm, arguments.rt_to_colour) == (3.0, 1.0)



def test_parse_arguments_names_the_report_after_the_annotation():
    """
    Title and output file fall back to the name of the annotation.

    Inputs:
        none=uses a fixed argument list
    outputs:
        none=the test only asserts
    """
    arguments = main.parse_arguments(
        [
            "--mzml_folder", str(HERE),
            "--rt-min", "0", "--rt-max", "1",
            "--mz-min", "0", "--mz-max", "1",
            "--annotation", "My ion",
        ]
    )

    assert arguments.title == "My ion in raw data"
    assert arguments.output == Path.cwd() / "My ion_peakmaps.html"



def test_parse_arguments_help_lists_the_options(capsys):
    """
    -h works and explains the displayed range as well as the coloured box.

    Inputs:
        capsys=pytest fixture that captures what argparse writes to stdout
    outputs:
        none=the test only asserts
    """
    with pytest.raises(SystemExit):
        main.parse_arguments(["--help"])

    help_text = capsys.readouterr().out

    assert "--rt-min" in help_text
    assert "--no-colour-all" in help_text
    assert "--rt-to-colour" in help_text



def test_parse_arguments_needs_the_ion_to_colour_a_selected_range(capsys):
    """
    --no-colour-all without an ion stops with a message that names the missing options.

    Inputs:
        capsys=pytest fixture that captures what argparse writes to stderr
    outputs:
        none=the test only asserts
    """
    with pytest.raises(SystemExit):
        main.parse_arguments(
            [
                "--mzml_folder", str(HERE),
                "--rt-min", "0", "--rt-max", "1",
                "--mz-min", "0", "--mz-max", "1",
                "--no-colour-all",
            ]
        )

    assert "--ion-mz" in capsys.readouterr().err



def test_parse_arguments_checks_the_folder_and_the_ranges(capsys):
    """
    A missing folder or an inverted range stops the tool.

    Inputs:
        capsys=pytest fixture that captures what argparse writes to stderr
    outputs:
        none=the test only asserts
    """
    with pytest.raises(SystemExit):
        main.parse_arguments(
            [
                "--mzml_folder", str(HERE / "no_such_folder"),
                "--rt-min", "0", "--rt-max", "1",
                "--mz-min", "0", "--mz-max", "1",
            ]
        )
    assert "not a folder" in capsys.readouterr().err

    with pytest.raises(SystemExit):
        main.parse_arguments(
            [
                "--mzml_folder", str(HERE),
                "--rt-min", "9", "--rt-max", "1",
                "--mz-min", "0", "--mz-max", "1",
            ]
        )
    assert "--rt-min" in capsys.readouterr().err

    with pytest.raises(SystemExit):
        main.parse_arguments(
            [
                "--mzml_folder", str(HERE),
                "--rt-min", "0", "--rt-max", "1",
                "--mz-min", "9", "--mz-max", "1",
            ]
        )
    assert "--mz-min" in capsys.readouterr().err



def test_parse_arguments_needs_the_folder(capsys):
    """
    Without a folder the parser stops instead of failing on a missing path.

    Inputs:
        capsys=pytest fixture that captures what argparse writes to stderr
    outputs:
        none=the test only asserts
    """
    with pytest.raises(SystemExit):
        main.parse_arguments(["--rt-min", "0", "--rt-max", "1", "--mz-min", "0", "--mz-max", "1"])

    assert "--mzml_folder" in capsys.readouterr().err



def test_main_writes_a_report_for_the_whole_range(mzml_folder, tmp_path, capsys):
    """
    The default run colours every peak, so no panel keeps a grey trace.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
        tmp_path=pytest fixture with an empty temporary folder
        capsys=pytest fixture that captures what main prints
    outputs:
        none=the test only asserts
    """
    output_file = tmp_path / "all.html"

    code = main.main(
        [
            "--mzml_folder", str(mzml_folder),
            "--rt-min", "457", "--rt-max", "460",
            "--mz-min", "325", "--mz-max", "332",
            "--pattern", "dummy_peak_a.mzml",
            "--output", str(output_file),
            "--annotation", "Cholesterol 1TMS",
        ]
    )
    config = peakmap_config(output_file.read_text(encoding="utf8"))

    assert code == 0 and output_file.is_file()
    assert "Saved plot to" in capsys.readouterr().out
    assert trace_names(config) == {"Cholesterol 1TMS"}



def test_main_writes_a_report_for_a_selected_range(mzml_folder, tmp_path):
    """
    --no-colour-all colours the ion box of every file and leaves the rest grey.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    output_file = tmp_path / "selected.html"

    code = main.main(
        [
            "--mzml_folder", str(mzml_folder),
            "--rt-min", "457", "--rt-max", "460",
            "--mz-min", "325", "--mz-max", "332",
            "--no-colour-all",
            "--ion-mz", "329.3203", "--ion-rt", "458.6873",
            "--annotation", "Cholesterol 1TMS",
            "--output", str(output_file),
        ]
    )
    html = output_file.read_text(encoding="utf8")
    config = peakmap_config(html)

    assert code == 0
    assert {"Cholesterol 1TMS", utils.UNKNOWN_LABEL} <= trace_names(config)
    assert "Cholesterol 1TMS in raw data" in html



def test_main_scales_the_axes_to_the_drawn_bars(mzml_folder, tmp_path):
    """
    The report axis follows the tallest bar the panels actually draw.

    The dummy files hold more peaks than the 50 x 50 bins of pyopenms_viz, so
    the tallest bar is a bin average below the tallest peak and the intensity
    axis of every panel has to match it.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
        tmp_path=pytest fixture with an empty temporary folder
    outputs:
        none=the test only asserts
    """
    output_file = tmp_path / "scaled.html"

    code = main.main(
        [
            "--mzml_folder", str(mzml_folder),
            "--rt-min", "455", "--rt-max", "462",
            "--mz-min", "324", "--mz-max", "333",
            "--output", str(output_file),
        ]
    )
    config = peakmap_config(output_file.read_text(encoding="utf8"))

    tallest_bar = max(
        z
        for panel in config["figures"]
        for trace in panel["data"]
        for z in (trace.get("z") or [])
        if z is not None
    )
    raw_max = max(
        df["intensity"].max()
        for _, df in utils.load_mzml_folder(str(mzml_folder), (455.0, 462.0), (324.0, 333.0))
    )

    assert code == 0
    # binning lowered the tallest bar below the tallest peak of the window
    assert tallest_bar < raw_max
    for panel in config["figures"]:
        assert panel["layout"]["scene"]["zaxis"]["range"] == pytest.approx([0.0, tallest_bar])



def test_main_reports_data_that_cannot_be_plotted(mzml_folder, tmp_path, capsys):
    """
    A window without any peak is reported instead of crashing.

    Inputs:
        mzml_folder=fixture with the dummy .mzml files
        tmp_path=pytest fixture with an empty temporary folder
        capsys=pytest fixture that captures what main prints
    outputs:
        none=the test only asserts
    """
    code = main.main(
        [
            "--mzml_folder", str(mzml_folder),
            "--rt-min", "1", "--rt-max", "2",
            "--mz-min", "1", "--mz-max", "2",
            "--no-colour-all",
            "--ion-mz", "1", "--ion-rt", "1",
            "--output", str(tmp_path / "empty.html"),
        ]
    )

    assert code == 1
    assert "Error" in capsys.readouterr().out
