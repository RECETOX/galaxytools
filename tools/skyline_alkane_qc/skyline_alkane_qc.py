import argparse
import colorsys

import matplotlib.pyplot as plt
import pandas as pd


REQUIRED_COLUMNS = [
    "File Name",
    "Molecule Name",
    "Mass Error PPM",
    "Retention Time",
]


def process_report(input_path):
    report = pd.read_csv(input_path, sep=None, engine="python")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in report.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    report = report[REQUIRED_COLUMNS].replace("#N/A", pd.NA)
    report["Mass Error PPM"] = pd.to_numeric(report["Mass Error PPM"], errors="coerce")
    report["Retention Time"] = pd.to_numeric(report["Retention Time"], errors="coerce")
    report = report.dropna(subset=["File Name", "Molecule Name"])
    report["File Name"] = report["File Name"].astype(str)
    report["Molecule Name"] = report["Molecule Name"].astype(str)

    mass_errors = report["Mass Error PPM"].dropna().abs()
    if mass_errors.empty:
        raise ValueError("The report contains no numeric mass errors.")
    if report["Retention Time"].dropna().empty:
        raise ValueError("The report contains no numeric retention times.")

    rt_deviation = (
        report.dropna(subset=["Retention Time"])
        .groupby("Molecule Name", sort=False)["Retention Time"]
        .agg(lambda values: (values.max() - values.min()) * 60)
        .rename("rt_diff (sec)")
        .reset_index()
    )
    summary = pd.DataFrame(
        {
            "rt_diff (sec)": [rt_deviation["rt_diff (sec)"].max()],
            "mass_error_ppm": [mass_errors.max()],
        }
    )
    return report, rt_deviation, summary


def plot_by_sample(report, column, ylabel, title, output_path, absolute=False, seconds=False):
    data = report.dropna(subset=[column]).copy()
    data["Sample Number"] = pd.to_numeric(
        data["File Name"].str.extract(r"^(\d+)")[0], errors="coerce"
    )
    if data["Sample Number"].notna().all():
        data["Sample Position"] = data["Sample Number"]
    else:
        sample_order = (
            data[["File Name", "Sample Number"]]
            .drop_duplicates()
            .sort_values(["Sample Number", "File Name"], na_position="last")["File Name"]
            .tolist()
        )
        sample_positions = {name: index for index, name in enumerate(sample_order)}
        data["Sample Position"] = data["File Name"].map(sample_positions)
    data["Plot Value"] = data[column]
    if absolute:
        data["Plot Value"] = data["Plot Value"].abs()
    if seconds:
        data["Plot Value"] = data["Plot Value"] * 60

    figure, axis = plt.subplots(figsize=(12, 6))
    molecules = data["Molecule Name"].drop_duplicates().tolist()
    colors = [
        colorsys.hsv_to_rgb(index / len(molecules), 0.4, 1.0)
        for index in range(len(molecules))
    ]
    for molecule, color in zip(molecules, colors):
        group = data[data["Molecule Name"] == molecule]
        group = group.sort_values("Sample Position")
        axis.plot(group["Sample Position"], group["Plot Value"], color=color, label=molecule)
    axis.set_xlabel("Sample Number")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend(title="Molecule Name", bbox_to_anchor=(1.02, 1), loc="upper left")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_rt_deviation(rt_deviation, output_path):
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(rt_deviation["Molecule Name"], rt_deviation["rt_diff (sec)"])
    axis.set_xlabel("Molecule Name")
    axis.set_ylabel("Maximum retention time deviation (sec)")
    axis.set_title("Retention time deviation by alkane")
    axis.tick_params(axis="x", labelrotation=45)
    for label in axis.get_xticklabels():
        label.set_ha("right")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description="Calculate Skyline alkane QC metrics and plots.")
    parser.add_argument("--input", required=True, help="Skyline report in CSV or TSV format")
    parser.add_argument("--summary", required=True, help="Output summary CSV")
    parser.add_argument("--mass_plot", required=True, help="Output mass accuracy plot")
    parser.add_argument("--rt_plot", required=True, help="Output retention time plot")
    parser.add_argument("--deviation_plot", required=True, help="Output RT deviation plot")
    args = parser.parse_args()

    report, rt_deviation, summary = process_report(args.input)
    summary.to_csv(args.summary, index=False)
    plot_by_sample(
        report,
        "Mass Error PPM",
        "Absolute mass error (ppm)",
        "Mass accuracy by alkane and sample",
        args.mass_plot,
        absolute=True,
    )
    plot_by_sample(
        report,
        "Retention Time",
        "Retention time (sec)",
        "Retention time by alkane and sample",
        args.rt_plot,
        seconds=True,
    )
    plot_rt_deviation(rt_deviation, args.deviation_plot)


if __name__ == "__main__":
    main()
