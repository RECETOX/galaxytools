import argparse
import csv
import sys


ARGUMENTS = {
    "Experiment": {"help": "Experiment name, no spaces.", "type": str},
    "Species": {"help": "Genus species from which samples are derived.", "type": str},
    "Sample": {"help": "Type of sample (e.g., serum, leaf).", "type": str},
    "Contributer": {"help": "Your or your PI's name.", "type": str},
    "platform": {"help": "Either GC-MS or LC-MS.", "type": str},
    "chrominst": {"help": "Model of LC/GC instrument.", "type": str},
    "msinst": {"help": "Model of MS instrument.", "type": str},
    "column": {"help": "Column description.", "type": str},
    "InletTemp": {"help": "Temperature of inlet.", "type": str},
    "TransferTemp": {"help": "Temperature of GC to MS transfer line.", "type": str},
    "mstype": {"help": "Type of mass spectrometer (one of QQQ, TOF, QTOF, Orbi, Q).", "type": str},
    "msmode": {"help": "Positive or negative ion mode.", "type": str},
    "ionization": {"help": "Ionization (EI, AP, or CI).", "type": str},
    "msscanrange": {"help": "Scan range used for acquisition.", "type": str},
    "scantime": {"help": "Time for each full scan spectrum (e.g. 0.2 seconds).", "type": float},
    "deriv": {"help": "Derivitization (TMS, TBDMS, or None).", "type": str},
    "MSlevs": {"help": "Number of levels of energy acquired - 1 typically.", "type": float},
    "solvA": {"help": "Solvent A composition.", "type": str},
    "solvB": {"help": "Solvent B composition.", "type": str},
    "CE1": {"help": "Collision energy of acquisition of MS data.", "type": str},
    "CE2": {"help": "Collision energy of acquisition for MSe/idMSMS data (when applicable).", "type": str},
    "colgas": {"help": "Gas used for collisional dissociation.", "type": str},
    "conevol": {"help": "Cone voltage used for acquisition.", "type": str}
}


def get_value(args, value, fill=True):
    if fill:
        return args[value]
    return "fill"


def write_gcms(csv_writer, args, fill=True):
    csv_writer.writerow(["", "", ""])
    csv_writer.writerow(["GC-MS", "", ""])

    gcms = ["chrominst", "msinst", "column", "InletTemp", "TransferTemp", "mstype", "msmode", "ionization",
            "msscanrange", "scantime", "deriv", "MSlevs"]
    for arg in gcms:
        csv_writer.writerow([arg, get_value(args, arg, fill=fill), ARGUMENTS[arg]["help"]])


def write_lcms(csv_writer, args, fill=True):
    csv_writer.writerow(["", "", ""])
    csv_writer.writerow(["LC-MS", "", ""])

    lcms = ["chrominst", "msinst", "column", "solvA", "solvB", "CE1", "CE2", "mstype", "msmode", "ionization", "colgas",
            "msscanrange", "conevol", "MSlevs"]
    for arg in lcms:
        csv_writer.writerow([arg, get_value(args, arg, fill=fill), ARGUMENTS[arg]["help"]])


def main(argv):
    parser = argparse.ArgumentParser(description="RAMClustR define experiment.")

    for arg in ARGUMENTS.keys():
        parser.add_argument(f"--{arg}", type=ARGUMENTS[arg]["type"], help=ARGUMENTS[arg]["help"])

    parser.add_argument("--output_file", type=str, help="Path to output csv file.")
    args = parser.parse_args().__dict__

    with open(args["output_file"], "w") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')

        csv_writer.writerow(["parameter", "Value", "Description"])
        csv_writer.writerow(["", "", ""])
        csv_writer.writerow(["Experimental Design", "", ""])

        general = ["Experiment", "Species", "Sample", "Contributer", "platform"]
        for arg in general:
            csv_writer.writerow([arg, args[arg], ARGUMENTS[arg]["help"]])

        if args["platform"] == "GC-MS":
            write_gcms(csv_writer, args)
            write_lcms(csv_writer, args, fill=False)
        elif args["platform"] == "LC-MS":
            write_gcms(csv_writer, args, fill=False)
            write_lcms(csv_writer, args)
        else:
            raise ValueError("Platform value incorrect, choose either GC-MS or LC-MS.")


if __name__ == "__main__":
    main(argv=sys.argv[1:])
