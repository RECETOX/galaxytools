#!/usr/bin/env python
"""
RDKit Structural Similarity Calculator

This script calculates structural similarity between compounds using RDKit fingerprints.
It accepts SMILES, InChI, or SDF files and outputs a table with similarity scores
and the input structures.
"""

import argparse
import logging
import re
import sys
from typing import Callable, List, Optional, Tuple

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, MACCSkeys, rdFingerprintGenerator

logger = logging.getLogger(__name__)


# Morgan fingerprint generator (ECFP-like) - using new API
_morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def get_morgan_fingerprint(mol: Chem.Mol):
    """Generate Morgan fingerprint for a molecule."""
    return _morgan_gen.GetFingerprint(mol)


def get_rdkit_fingerprint(mol: Chem.Mol):
    """Generate RDKit fingerprint for a molecule."""
    return AllChem.RDKFingerprint(mol, maxPath=7, fpSize=2048)


def get_maccs_fingerprint(mol: Chem.Mol):
    """Generate MACCS keys fingerprint for a molecule."""
    return MACCSkeys.GenMACCSKeys(mol)


def get_fingerprint(mol: Chem.Mol, fingerprint_type: str):
    """
    Generate fingerprint for a molecule based on specified type.

    Args:
        mol: RDKit Mol object
        fingerprint_type: Type of fingerprint ("Morgan", "RDKit", or "MACCS")

    Returns:
        Fingerprint bit vector or None if molecule is invalid
    """
    if mol is None:
        return None

    if fingerprint_type == "Morgan":
        return get_morgan_fingerprint(mol)
    elif fingerprint_type == "RDKit":
        return get_rdkit_fingerprint(mol)
    elif fingerprint_type == "MACCS":
        return get_maccs_fingerprint(mol)
    else:
        raise ValueError(f"Unknown fingerprint type: {fingerprint_type}")


def detect_structure_type(structure_str: str) -> Optional[str]:
    """
    Detect whether a string is a SMILES or InChI representation.

    Args:
        structure_str: Structure string to analyze

    Returns:
        'SMILES', 'InChI', or None if undetectable
    """
    if not structure_str:
        return None

    structure_str = str(structure_str).strip()

    # Check for InChI prefix
    if structure_str.startswith("InChI=") or structure_str.startswith("InChI"):
        return "InChI"

    # Simple heuristic for SMILES: contains common organic element symbols
    # and doesn't start with InChI
    smiles_pattern = r'^[CNOcSsNnPpFxClBrIa-zA-Z0-9@+\-\[\]()\\/=]+$'
    if re.match(smiles_pattern, structure_str) and len(structure_str) > 1:
        return "SMILES"

    return None


def parse_structure(structure_str: str) -> Optional[Tuple[Chem.Mol, str]]:
    """
    Parse a SMILES or InChI string into an RDKit Mol object.
    Auto-detects the structure type.

    Args:
        structure_str: SMILES or InChI string

    Returns:
        Tuple of (RDKit Mol object, detected type) or None if parsing fails
    """
    if not structure_str:
        return None

    structure_str = str(structure_str).strip()

    # Try to detect type
    detected_type = detect_structure_type(structure_str)

    if detected_type == "InChI":
        mol = Chem.MolFromInchi(structure_str)
        if mol is not None:
            return (mol, "InChI")
    elif detected_type == "SMILES":
        mol = Chem.MolFromSmiles(structure_str)
        if mol is not None:
            return (mol, "SMILES")
    else:
        # Try SMILES first, then InChI
        mol = Chem.MolFromSmiles(structure_str)
        if mol is not None:
            return (mol, "SMILES")

        mol = Chem.MolFromInchi(structure_str)
        if mol is not None:
            return (mol, "InChI")

    logger.warning(f"Could not parse structure: {structure_str[:50]}...")
    return None


def calculate_similarity(fp1, fp2, metric: str) -> float:
    """
    Calculate similarity between two fingerprints using the specified metric.

    Args:
        fp1: First fingerprint
        fp2: Second fingerprint
        metric: Similarity metric name

    Returns:
        Similarity score (0-1)
    """
    if metric == "tanimoto":
        return DataStructs.TanimotoSimilarity(fp1, fp2)
    elif metric == "dice":
        return DataStructs.DiceSimilarity(fp1, fp2)
    elif metric == "cosine":
        return DataStructs.CosineSimilarity(fp1, fp2)
    elif metric == "soergel":
        return DataStructs.SoergelSimilarity(fp1, fp2)
    elif metric == "kulczynski":
        return DataStructs.KulczynskiSimilarity(fp1, fp2)
    elif metric == "mcconnaughey":
        return DataStructs.McConnaugheySimilarity(fp1, fp2)
    else:
        raise ValueError(f"Unknown similarity metric: {metric}")


def load_compounds_from_smi_inchi(filepath: str) -> Tuple[List[Tuple[str, Chem.Mol]], str]:
    """
    Load compounds from SMI or INCHI file.

    Args:
        filepath: Path to input file

    Returns:
        Tuple of (list of (structure_string, Mol) tuples, detected structure type)
    """
    compounds = []
    detected_type = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments

            result = parse_structure(line)
            if result:
                mol, struct_type = result
                if detected_type is None:
                    detected_type = struct_type
                compounds.append((line, mol))

    if not compounds:
        raise ValueError(f"No valid compounds found in {filepath}!")

    logger.info(f"Loaded {len(compounds)} compounds from {filepath} ({detected_type})")
    return compounds, detected_type


def load_compounds_from_sdf(filepath: str) -> Tuple[List[Tuple[str, Chem.Mol]], str]:
    """
    Load compounds from SDF file. Extracts SMILES from the data block.

    Args:
        filepath: Path to SDF file

    Returns:
        Tuple of (list of (structure_string, Mol) tuples, detected structure type)
    """
    compounds = []
    detected_type = None

    suppl = Chem.SDMolSupplier(filepath, removeHs=False)

    for mol in suppl:
        if mol is None:
            continue

        # Try to get SMILES from the molecule
        smiles = Chem.MolToSmiles(mol)
        if smiles:
            compounds.append((smiles, mol))
            if detected_type is None:
                detected_type = "SMILES"

    if not compounds:
        raise ValueError(f"No valid compounds found in {filepath}!")

    logger.info(f"Loaded {len(compounds)} compounds from {filepath} ({detected_type})")
    return compounds, detected_type


# Mapping from file type to loader function
FILE_LOADERS: dict[str, Callable[[str], Tuple[List[Tuple[str, Chem.Mol]], str]]] = {
    "smi": load_compounds_from_smi_inchi,
    "inchi": load_compounds_from_smi_inchi,
    "sdf": load_compounds_from_sdf,
}


def main(argv):
    parser = argparse.ArgumentParser(
        description="Calculate structural similarity between compounds using RDKit"
    )

    parser.add_argument(
        "--queries", type=str, required=True,
        help="Path to query compounds file"
    )
    parser.add_argument(
        "--queries-type", type=str, required=True, choices=["smi", "inchi", "sdf"],
        help="Format of query compounds file (smi, inchi, or sdf)"
    )
    parser.add_argument(
        "--references", type=str, required=True,
        help="Path to reference compounds file"
    )
    parser.add_argument(
        "--references-type", type=str, required=True, choices=["smi", "inchi", "sdf"],
        help="Format of reference compounds file (smi, inchi, or sdf)"
    )
    parser.add_argument(
        "--similarity-metric", type=str, default="tanimoto",
        choices=["tanimoto", "dice", "cosine", "soergel", "kulczynski", "mcconnaughey"],
        help="Similarity metric to use (default: tanimoto)"
    )
    parser.add_argument(
        "--fingerprint-type", type=str, default="Morgan",
        choices=["Morgan", "RDKit", "MACCS"],
        help="Type of fingerprint to use (default: Morgan)"
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Output TSV file path for similarity results"
    )

    args = parser.parse_args(argv)

    try:
        # Get loader functions based on file types
        query_loader = FILE_LOADERS.get(args.queries_type)
        ref_loader = FILE_LOADERS.get(args.references_type)

        if query_loader is None:
            raise ValueError(f"Unsupported query file type: {args.queries_type}")
        if ref_loader is None:
            raise ValueError(f"Unsupported reference file type: {args.references_type}")

        # Load compounds using the specified loaders (ignoring file extension)
        logger.info("Loading query compounds...")
        query_compounds, query_type = query_loader(args.queries)

        logger.info("Loading reference compounds...")
        ref_compounds, ref_type = ref_loader(args.references)

        # Determine output structure type preference
        output_type = query_type if query_type else ref_type
        logger.info(f"Using structure type: {output_type}")

        # Generate fingerprints
        logger.info(f"Generating {args.fingerprint_type} fingerprints...")
        query_fps = [get_fingerprint(mol, args.fingerprint_type) for _, mol in query_compounds]
        ref_fps = [get_fingerprint(mol, args.fingerprint_type) for _, mol in ref_compounds]

        # Remove invalid entries
        valid_queries = [(comp[0], fp) for comp, fp in zip(query_compounds, query_fps) if fp is not None]
        valid_refs = [(comp[0], fp) for comp, fp in zip(ref_compounds, ref_fps) if fp is not None]

        if not valid_queries:
            raise ValueError("No valid query compounds with usable fingerprints!")
        if not valid_refs:
            raise ValueError("No valid reference compounds with usable fingerprints!")

        logger.info(
            f"Valid compounds - Queries: {len(valid_queries)}, References: {len(valid_refs)}"
        )

        logger.info(f"Calculating {args.similarity_metric} similarity...")

        # Calculate all pairwise similarities and build output
        results = []
        for q_struct, q_fp in valid_queries:
            for r_struct, r_fp in valid_refs:
                sim = calculate_similarity(q_fp, r_fp, args.similarity_metric)
                results.append({
                    "query_structure": q_struct,
                    "reference_structure": r_struct,
                    "similarity": sim
                })

        # Create output - write directly to avoid pandas dependency
        with open(args.output, 'w') as f:
            f.write("similarity\tquery_structure\treference_structure\n")
            for r in results:
                f.write(f"{r['similarity']}\t{r['query_structure']}\t{r['reference_structure']}\n")

        logger.info(f"Similarity results written to {args.output}")
        logger.info(f"Total comparisons: {len(results)}")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
