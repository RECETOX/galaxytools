from aoptk.normalization.provide_mesh_term_dataframe_from_xml import ProvideMeshTermDataframeFromXML
import argparse
import pandas as pd


def provide_normalization_dataframe(xml_path: str) -> pd.DataFrame:
    """Generate a MeSH terms dataframe from an XML file.

    Args:
        xml_path (str): Path to the MeSH XML file.
    """
    return ProvideMeshTermDataframeFromXML(xml_path).provide_normalization_dataframe()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MeSH terms dataframe from XML")
    parser.add_argument("--xml_path", required=True, help="Path to the MeSH XML file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    mesh_terms_df = provide_normalization_dataframe(args.xml_path)
