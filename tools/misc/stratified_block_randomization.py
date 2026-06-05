#!/usr/bin/env python3
"""Hierarchical proportional block assignment.

Samples are split into blocks of size m (the last block may be smaller).
Balancing is done by levels:
1. Factor 1 is matched proportionally in every block.
2. Within each factor-1 slice, factor 2 is matched proportionally.
3. The same logic is applied recursively for additional factors.

Integer quotas are computed with largest-remainder rounding while enforcing
exact totals across both dimensions.
"""

import argparse
from dataclasses import dataclass
import sys

import numpy as np
import pandas as pd


class StudyDesignerError(Exception):
    """Base exception for recoverable tool errors."""


@dataclass(frozen=True)
class StudyDesignConfig:
    """Runtime configuration for the study designer."""

    input_path: str
    output_path: str
    block_size: int
    factors: list[str]
    sample_col: str
    columns_mode: str
    seed: int
    summary_path: str | None


def parse_args() -> StudyDesignConfig:
    parser = argparse.ArgumentParser(
        description="Create balanced random blocks preserving factor proportions."
    )
    parser.add_argument("--input", required=True, help="Input TSV file with samples.")
    parser.add_argument(
        "--block_size",
        type=int,
        required=True,
        help=(
            "Target size per block. Blocks are created sequentially from this size; "
            "the final block may be smaller."
        ),
    )
    parser.add_argument(
        "--factors",
        nargs="+",
        required=True,
        help="Column names to balance on (e.g. --factors group status).",
    )
    parser.add_argument(
        "--sample_col",
        default="sample",
        help="Name of the sample identifier column (default: sample).",
    )
    parser.add_argument(
        "--columns_mode",
        choices=["names", "indices"],
        default="names",
        help=(
            "Interpret --factors/--sample_col as column names (default) or as "
            "1-based column indices. In 'indices' mode, --factors may be a "
            "comma-separated list (e.g. 2,3) or space-separated values."
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output TSV file: original columns plus a 'block' column.",
    )
    parser.add_argument(
        "--summary",
        default=None,
        help="Optional path to write a per-block factor-count summary TSV.",
    )
    args = parser.parse_args()
    return StudyDesignConfig(
        input_path=args.input,
        output_path=args.output,
        block_size=args.block_size,
        factors=args.factors,
        sample_col=args.sample_col,
        columns_mode=args.columns_mode,
        seed=args.seed,
        summary_path=args.summary,
    )


def load_and_prepare_input(input_path: str) -> pd.DataFrame:
    """Load input data as-is from TSV."""
    df = pd.read_csv(input_path, sep="\t").reset_index(drop=True)
    return df


def add_original_index(df: pd.DataFrame) -> pd.DataFrame:
    """Add a persistent original row index column."""
    df = df.copy()
    df.insert(0, "original_index", df.index)
    return df


def _index_token_to_name(columns: list[str], token: str, arg_name: str) -> str:
    """Convert one 1-based index token (e.g. '3' or 'c3') to a column name."""
    t = token.strip()
    if t.lower().startswith("c"):
        t = t[1:]

    if not t.isdigit():
        raise StudyDesignerError(f"{arg_name}: invalid column index token '{token}'")

    idx = int(t)
    if idx < 1 or idx > len(columns):
        raise StudyDesignerError(
            f"{arg_name}: column index {idx} out of range (1..{len(columns)})"
        )
    return columns[idx - 1]


def resolve_column_args(
    df: pd.DataFrame,
    factors: list[str],
    sample_col: str,
    columns_mode: str,
) -> tuple[list[str], str]:
    """Resolve factors/sample column arguments from names or 1-based indices."""
    if columns_mode == "names":
        return factors, sample_col

    columns = list(df.columns)

    factor_tokens: list[str] = []
    for token in factors:
        factor_tokens.extend([x for x in token.split(",") if x.strip()])

    resolved_factors = [
        _index_token_to_name(columns, token, "--factors") for token in factor_tokens
    ]
    resolved_sample_col = _index_token_to_name(columns, sample_col, "--sample_col")
    return resolved_factors, resolved_sample_col


def validate_inputs(
    df: pd.DataFrame,
    factors: list[str],
    sample_col: str,
    block_size: int,
) -> None:
    """Validate required columns and basic argument constraints."""
    missing = [f for f in factors + [sample_col] if f not in df.columns]
    if missing:
        raise StudyDesignerError(f"columns not found in input: {missing}")

    if block_size is not None and block_size < 1:
        raise StudyDesignerError("--block_size must be >= 1")

    na_mask = df.isna()
    blank_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    object_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in object_cols:
        blank_mask[col] = df[col].astype("string").str.strip().eq("")

    missing_mask = na_mask | blank_mask
    if missing_mask.any().any():
        missing_by_column = missing_mask.sum()
        missing_by_column = missing_by_column[missing_by_column > 0]
        details = ", ".join(
            [f"{col}: {int(count)}" for col, count in missing_by_column.items()]
        )
        raise StudyDesignerError(
            "input table contains missing values; please clean the input first. "
            f"Missing counts by column: {details}"
        )


def normalize_factor_columns(
    df: pd.DataFrame,
    factors: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Create normalized internal factor columns used for stratification."""
    work = df.copy()
    strat_cols = []
    for factor in factors:
        col = f"_strat_{factor}"
        work[col] = work[factor].astype(str).str.strip().str.lower()
        strat_cols.append(col)
    return work, strat_cols


def compute_block_sizes(total_samples: int, block_size: int) -> dict[int, int]:
    """Compute block size map where the final block may be smaller."""
    n_blocks = (total_samples + block_size - 1) // block_size
    block_ids = list(range(n_blocks))
    return {b: min(block_size, total_samples - b * block_size) for b in block_ids}


def _allocate_matrix(
    row_totals: dict[int, int],
    col_totals: dict[str, int],
    rng: np.random.Generator,
    context: str = "",
) -> dict[int, dict[str, int]]:
    """Allocate integer matrix matching row/column margins.

    Uses fractional quota target + floor + largest-remainder increments while
    respecting both row and column deficits.
    """
    row_keys = list(row_totals.keys())
    col_keys = list(col_totals.keys())

    row = np.array([row_totals[k] for k in row_keys], dtype=int)
    col = np.array([col_totals[k] for k in col_keys], dtype=int)
    total = int(row.sum())

    if total == 0:
        return {rk: {ck: 0 for ck in col_keys} for rk in row_keys}

    col_total = int(col.sum())
    if total != col_total:
        raise StudyDesignerError(
            "ERROR: internal allocation mismatch (row/column totals differ) "
            f"at {context or 'root'}: row_total={total}, col_total={col_total}."
        )

    quotas = np.outer(row, col) / total
    alloc = np.floor(quotas).astype(int)
    frac = quotas - alloc

    row_def = row - alloc.sum(axis=1)
    col_def = col - alloc.sum(axis=0)

    while int(row_def.sum()) > 0:
        best_score = None
        best_cell = None
        for i in range(len(row_keys)):
            if row_def[i] <= 0:
                continue
            for j in range(len(col_keys)):
                if col_def[j] <= 0:
                    continue
                # Tiny random tie-breaker keeps output reproducible with seed.
                score = frac[i, j] + float(rng.random()) * 1e-9
                if best_score is None or score > best_score:
                    best_score = score
                    best_cell = (i, j)

        if best_cell is None:
            raise StudyDesignerError("internal allocation failed to resolve deficits")

        i, j = best_cell
        alloc[i, j] += 1
        row_def[i] -= 1
        col_def[j] -= 1

    return {
        row_keys[i]: {col_keys[j]: int(alloc[i, j]) for j in range(len(col_keys))}
        for i in range(len(row_keys))
    }


def _hierarchical_leaf_targets(
    df_subset: pd.DataFrame,
    factors: list[str],
    block_totals: dict[int, int],
    rng: np.random.Generator,
    prefix: tuple[str, ...] = (),
) -> dict[tuple[str, ...], dict[int, int]]:
    """Recursively allocate counts for each factor combination per block."""
    current = factors[0]
    level_counts = df_subset[current].value_counts(sort=False, dropna=False).to_dict()
    level_alloc = _allocate_matrix(
        block_totals,
        level_counts,
        rng,
        context="/".join(prefix) if prefix else factors[0],
    )

    if len(factors) == 1:
        leaf_targets = {}
        for level in level_counts:
            leaf = prefix + (level,)
            leaf_targets[leaf] = {
                block: level_alloc[block][level] for block in block_totals.keys()
            }
        return leaf_targets

    leaf_targets = {}
    for level in level_counts:
        sub_df = df_subset[df_subset[current] == level]
        sub_block_totals = {
            block: level_alloc[block][level] for block in block_totals.keys()
        }
        sub_targets = _hierarchical_leaf_targets(
            sub_df,
            factors[1:],
            sub_block_totals,
            rng,
            prefix=prefix + (level,),
        )
        leaf_targets.update(sub_targets)

    return leaf_targets


def assign_factor_targets_to_blocks(
    work: pd.DataFrame,
    strat_cols: list[str],
    block_sizes: dict[int, int],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Assign block ids by matching hierarchical proportional targets."""
    block_ids = list(block_sizes.keys())

    work["block"] = -1

    # Compute exact per-block targets for every factor combination using
    # hierarchical proportional allocation.
    leaf_targets = _hierarchical_leaf_targets(work, strat_cols, block_sizes, rng)

    # Group sample indices by full factor combination and assign per block.
    grouped = work.groupby(strat_cols, sort=False)
    for key, group_df in grouped:
        leaf = key if isinstance(key, tuple) else (key,)
        indices = group_df.index.to_numpy().copy()
        rng.shuffle(indices)

        offset = 0
        block_plan = leaf_targets[leaf]
        for b in block_ids:
            take = block_plan[b]
            if take > 0:
                chosen = indices[offset : offset + take]
                work.loc[chosen, "block"] = b
                offset += take

        if offset != len(indices):
            raise StudyDesignerError(
                "internal assignment mismatch while distributing samples "
                f"for factor level {leaf}."
            )

    return work


def shuffle_within_blocks(work: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Shuffle order inside blocks and add 1-based position within each block."""

    # Randomize sample order within each block (reproducible with --seed).
    # This keeps block composition intact while removing any deterministic
    # ordering that comes from allocation steps.
    work["_within_block_shuffle"] = rng.random(len(work))
    work = work.sort_values(["block", "_within_block_shuffle"]).copy()

    # Position of each sample inside its block after shuffling (1-based).
    work["block_position"] = work.groupby("block").cumcount() + 1

    return work


def assign_blocks(
    df: pd.DataFrame,
    factors: list[str],
    block_size: int,
    seed: int,
) -> pd.DataFrame:
    """Orchestrate full assignment pipeline."""
    rng = np.random.default_rng(seed)

    work, strat_cols = normalize_factor_columns(df, factors)
    block_sizes = compute_block_sizes(len(work), block_size)
    work = assign_factor_targets_to_blocks(work, strat_cols, block_sizes, rng)
    work = shuffle_within_blocks(work, rng)

    # Drop internal stratification columns
    work.drop(columns=strat_cols + ["_within_block_shuffle"], inplace=True)
    return work


def build_summary_tables(
    df: pd.DataFrame,
    factors: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, int, int]:
    """Build summary tables for printing and optional export."""
    assigned = df[df["block"] >= 0]
    cols = ["block"] + factors
    counts = assigned.groupby(cols).size().reset_index(name="n")

    pivot = counts.pivot_table(index=factors, columns="block", values="n", fill_value=0)
    pivot = pivot.astype(int)

    sizes = assigned.groupby("block").size()
    last_block = df["block"].max()
    last_size = int((df["block"] == last_block).sum())
    full_blocks = df[df["block"] < last_block].groupby("block").size()
    full_block_size = int(full_blocks.iloc[0]) if len(full_blocks) else 0

    return counts, pivot, sizes, full_block_size, last_size


def print_summary(
    df: pd.DataFrame, factors: list[str], summary_path: str | None = None
) -> None:
    counts, pivot, sizes, full_block_size, last_size = build_summary_tables(df, factors)

    print("\n=== Block assignment counts ===")
    print(pivot.to_string())

    print("\n=== Block sizes ===")
    print(sizes.to_string())

    if full_block_size:
        print(f"\nFull block size : {full_block_size}")
    print(f"Last block size : {last_size}")

    if summary_path:
        counts.to_csv(summary_path, sep="\t", index=False)
        print(f"\nSummary written to: {summary_path}")


def main():
    cfg = parse_args()
    try:
        df = load_and_prepare_input(cfg.input_path)
        factors, sample_col = resolve_column_args(
            df,
            cfg.factors,
            cfg.sample_col,
            cfg.columns_mode,
        )
        validate_inputs(df, factors, sample_col, cfg.block_size)

        df = add_original_index(df)

        result = assign_blocks(
            df,
            factors=factors,
            block_size=cfg.block_size,
            seed=cfg.seed,
        )

        result.to_csv(cfg.output_path, sep="\t", index=False)
        print(f"Output written to: {cfg.output_path}")

        print_summary(result, factors, cfg.summary_path)
    except StudyDesignerError as exc:
        sys.exit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
