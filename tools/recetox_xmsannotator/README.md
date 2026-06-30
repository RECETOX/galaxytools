# recetox-xMSannotator Galaxy Tools

This directory contains the split recetox-xMSannotator tools, decomposed from the original monolithic `recetox_xmsannotator_advanced.xml` tool into 12 focused, reusable components.

## Overview

The original xMSannotator tool performed advanced metabolite annotation through a multi-step pipeline. This decomposition provides:

- **Modularity**: Each pipeline step is now an independent tool
- **Flexibility**: Users can use individual steps or chain them as needed
- **Reusability**: Tools can be combined in custom workflows
- **Maintainability**: Smaller, focused tools are easier to maintain

## Tool List

| Issue | Tool File | Description |
|-------|-----------|-------------|
| #612 | [recetox_xmsannotator_simple_annotation.xml](recetox_xmsannotator_simple_annotation.xml) | Initial peak-compound matching based on mass tolerance |
| #613 | [recetox_xmsannotator_compute_mass_defect.xml](recetox_xmsannotator_compute_mass_defect.xml) | Compute mass defect column for peaks/annotations |
| #614 | [recetox_xmsannotator_compute_peak_correlations.xml](recetox_xmsannotator_compute_peak_correlations.xml) | Calculate correlation matrix between peaks |
| #615 | [recetox_xmsannotator_compute_peak_modules.xml](recetox_xmsannotator_compute_peak_modules.xml) | Group correlated peaks into modules |
| #616 | [recetox_xmsannotator_compute_rt_modules.xml](recetox_xmsannotator_compute_rt_modules.xml) | Cluster peaks by retention time |
| #617 | [recetox_xmsannotator_compute_isotopes.xml](recetox_xmsannotator_compute_isotopes.xml) | Detect and assign isotopic peaks |
| #618 | [recetox_xmsannotator_reformat_annotation.xml](recetox_xmsannotator_reformat_annotation.xml) | Prepare data for chemscore computation |
| #619 | [recetox_xmsannotator_compute_chemscore.xml](recetox_xmsannotator_compute_chemscore.xml) | Compute chemical confidence scores |
| #620 | [recetox_xmsannotator_pathway_matching.xml](recetox_xmsannotator_pathway_matching.xml) | Match annotations to metabolic pathways |
| #621 | [recetox_xmsannotator_compute_confidence_levels.xml](recetox_xmsannotator_compute_confidence_levels.xml) | Assign MSI-style confidence levels |
| #622 | [recetox_xmsannotator_redundancy_filtering.xml](recetox_xmsannotator_redundancy_filtering.xml) | Filter redundant low-scoring annotations |

## Standard Pipeline Execution Order

For users who want to replicate the original advanced annotation workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STANDARD PIPELINE ORDER                          │
└─────────────────────────────────────────────────────────────────────┘

Input: metadata_table + intensity_table + compound_table + adduct_table
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Simple Annotation (#612)                                     │
│    - Match peaks to compounds using mass tolerance              │
│    - Output: annotation table                                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Compute Mass Defect (#613)                                   │
│    - Add mass defect column to annotation                       │
│    - Output: annotation with MD column                          │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Compute Peak Correlations (#614)                             │
│    - Calculate correlation matrix from intensity profiles       │
│    - Output: correlation matrix                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Compute Peak Modules (#615)                                  │
│    - Group highly correlated peaks                              │
│    - Requires: intensity matrix + correlation matrix            │
│    - Output: peak module assignments                            │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Compute RT Modules (#616)                                    │
│    - Cluster peaks by retention time                            │
│    - Requires: peak table with module assignments               │
│    - Output: RT cluster assignments                             │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Compute Mass Defect (#613) [Second Pass]                     │
│    - Recompute mass defect on enriched peak table               │
│    - Output: peak table with updated MD                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Compute Isotopes (#617)                                      │
│    - Detect isotopic peaks                                      │
│    - Requires: annotation + adduct weights + peak table         │
│    - Output: annotation with isotope groups                     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Reformat Annotation (#618)                                   │
│    - Prepare annotation and correlation for scoring             │
│    - Output: reformatted annotation + global correlation        │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Compute Chemscore (#619)                                     │
│    - Calculate confidence scores                                │
│    - Requires: reformatted annotation + global cor + adduct wt  │
│    - Output: annotation with chemscores                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. Compute Confidence Levels (#621)                            │
│     - Assign MSI-style confidence levels                        │
│     - Output: annotation with confidence levels                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│ 11a. Pathway Matching       │   │ 11b. Skip (Optional)        │
│     (#620 - Optional)       │   │                             │
│     - Add pathway context   │   │                             │
│     - Boost scores          │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. Redundancy Filtering (#622 - Optional)                      │
│     - Remove low-scoring redundant annotations                  │
│     - Output: Final clean annotation set                        │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                           Final Annotation Output
```

## Data Flow Diagram

```
metadata_table ─┐
                │
intensity_table─┼──► [612 Simple Annotation] ──► annotation
                │              │
compound_table──┘              ▼
                       [613 Mass Defect] ──► annotation+MD
                                │
                                ▼
adduct_table ──┐               [614 Peak Correlations] ──► correlation_matrix
               │                          │
               └──────────────────────────┼────────────────┐
                                          ▼                │
                                 [615 Peak Modules]        │
                                       │                   │
                                       ▼                   │
                                 [616 RT Modules]          │
                                       │                   │
                                       ▼                   │
                                 [613 Mass Defect] ◄───────┘
                                       │
                                       ▼
                                 [617 Isotopes]
                                       │
                                       ▼
                                 [618 Reformat] ──► global_cor
                                       │
                                       ▼
                                 [619 Chemscore]
                                       │
                                       ▼
                           [621 Confidence Levels]
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     │
              [620 Pathway Matching] ◄───(optional)──────┘
                    │
                    ▼
              [622 Redundancy Filtering] ◄───(optional)
                    │
                    ▼
              Final Annotations
```

## Common Workflows

### Quick Annotation (Minimal Steps)

For fast, basic annotation without advanced features:

```
Simple Annotation → Compute Chemscore → Redundancy Filtering
```

### Full Confidence Assessment

For comprehensive annotation with confidence levels:

```
Simple Annotation → Mass Defect → Peak Correlations → Peak Modules →
RT Modules → Isotopes → Reformat → Chemscore → Confidence Levels
```

### Pathway-Aware Analysis

For biological interpretation:

```
[Full Pipeline] → Pathway Matching → Redundancy Filtering
```

## Input/Output Formats

All tools support:
- **Input**: Parquet (.parquet), CSV (.csv)
- **Output**: Same format as primary input (preserved via `<change_format>`)

## Shared Components

### macros.xml

Common definitions used across all tools:
- Creator metadata
- Requirements (r-recetox-xmsannotator package)
- Citations
- EDAM ontology terms
- Common parameter definitions

### utils.R

Shared R utility functions:
- `load_table()`: Load CSV or Parquet files
- `save_table()`: Save tables in appropriate format
- `create_filter_by_adducts()`: Parse adduct filter strings
- `create_peak_table()`: Combine metadata and intensity tables

## Migration from Monolithic Tool

### Original Tool Deprecation

The original `recetox_xmsannotator_advanced.xml` is retained for backward compatibility but marked as deprecated.

### Migration Guide

| Old Parameter | New Tool Equivalent |
|---------------|---------------------|
| All parameters in sequence | Chain individual tools |
| Single output | Multiple intermediate outputs available |
| Fixed pipeline | Customizable workflow |

### Example Migration

**Old (single tool):**
```xml
<tool id="recetox_xmsannotator_advanced" ...>
    <param name="metadata_table" .../>
    <param name="intensity_table" .../>
    <!-- all other params -->
</tool>
```

**New (workflow):**
```xml
<workflow>
    <step type="recetox_simple_annotation">...</step>
    <step type="recetox_compute_mass_defect">...</step>
    <step type="recetox_compute_peak_correlations">...</step>
    <!-- continue chain -->
</workflow>
```

## Testing

Each tool includes test cases in its XML definition:
- Parquet format tests
- CSV format tests
- Edge case tests (various parameter combinations)

Run tests with:
```bash
planemo test tools/recetox_xmsannotator/*.xml
```

## Version Information

- **Tool Version**: @TOOL_VERSION@+galaxy1 (0.10.0+galaxy1)
- **R Package**: r-recetox-xmsannotator >= 0.10.0
- **Profile**: 23.0

## Citations

Novotný, J., Čech, M., & Troják, M. (2024). recetox-xMSannotator: Advanced metabolite annotation tool. Analytical Chemistry. DOI: 10.1021/acs.analchem.6b01214

## Contributors

- Jiří Novotný (ORCID: 0000-0001-5449-3523)
- Martin Čech (ORCID: 0000-0002-9318-1781)
- Matej Troják (ORCID: 0000-0003-0841-2707)

Organization: RECETOX MUNI (https://www.recetox.muni.cz/)

## Related Issues

- Main issue: #781 - Split recetox-xmsannotator tool
- Sub-issues: #612-#622 (individual tools)

## License

MIT License
