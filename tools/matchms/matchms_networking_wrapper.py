import argparse
import sys

from matchms.importing import load_scores
from matchms.similarity import SimilarityNetwork


def main(argv):
    parser = argparse.ArgumentParser(description="Create network-graph from similarity scores.")
    parser.add_argument("scores", type=str, help="Path to matchMS similarity-scores .json file.")
    parser.add_argument("graph_format", type="str", help="Format of the output similarity network.")
    parser.add_argument("identifier", type=str, help="Unique metadata identifier of each spectrum from which scores are computed.")
    parser.add_argument("top_n", type=int, help="Number of highest-score edges to keep.")
    parser.add_argument("max_links", type=int, help="Maximum number of links to add per node.")
    parser.add_argument("score_cutoff", type=float, help="Minimum similarity score value to link two spectra.")
    parser.add_argument("link_method", type=str, help="Method for selecting top N edges for each node.")
    parser.add_argument("keep_unconnected_nodes", type=bool, help="Keep unconnected nodes in the network.")

    scores = load_scores(parser.scores)

    network = SimilarityNetwork(identifier_key=parser.identifier,
        top_n=parser.top_n,
        max_links=parser.max_links,
        score_cutoff=parser.score_cutoff,
        link_method=parser.link_method,
        keep_unconected_nodes=parser.keep_unconnected_nodes)
    network.create_network(scores)
    network.export_to_file(filename=parser.output_filename, graph_format=parser.graph_format)

    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
