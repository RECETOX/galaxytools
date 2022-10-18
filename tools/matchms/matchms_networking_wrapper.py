import argparse
import sys

from matchms.importing import scores_from_json
from matchms.networking import SimilarityNetwork


def main(argv):
    parser = argparse.ArgumentParser(description="Create network-graph from similarity scores.")
    parser.add_argument("--graph_format", type=str, help="Format of the output similarity network.")
    parser.add_argument("--identifier", type=str, help="Unique metadata identifier of each spectrum from which scores are computed.")
    parser.add_argument("--top_n", type=int, help="Number of highest-score edges to keep.")
    parser.add_argument("--max_links", type=int, help="Maximum number of links to add per node.")
    parser.add_argument("--score_cutoff", type=float, help="Minimum similarity score value to link two spectra.")
    parser.add_argument("--link_method", type=str, help="Method for selecting top N edges for each node.")
    parser.add_argument("--keep_unconnected_nodes", help="Keep unconnected nodes in the network.", action="store_true")
    parser.add_argument("scores", type=str, help="Path to matchMS similarity-scores .json file.")
    parser.add_argument("output_filename", type=str, help="Path where to store the output similarity network.")
    args = parser.parse_args()

    scores = scores_from_json(args.scores)

    network = SimilarityNetwork(identifier_key=args.identifier,
                                top_n=args.top_n,
                                max_links=args.max_links,
                                score_cutoff=args.score_cutoff,
                                link_method=args.link_method,
                                keep_unconnected_nodes=args.keep_unconnected_nodes)

    network.create_network(scores)
    network.export_to_file(filename=args.output_filename, graph_format=args.graph_format)

    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
    pass
