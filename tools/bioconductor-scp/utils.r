# Export intermediate results
# Function to export a single assay with metadata
export_assay_with_metadata <- function(qf, assay_name) {
    # Extract assay data, row metadata, and col metadata
    assay_data <- SummarizedExperiment::assay(qf[[assay_name]])
    row_metadata <- as.data.frame(SummarizedExperiment::rowData(qf[[assay_name]]))
    col_metadata <- as.data.frame(SummarizedExperiment::colData(qf))
    # Combine row metadata with assay data
    export_data <- cbind(RowNames = rownames(assay_data), row_metadata, as.data.frame(assay_data))
    # Save the table to a CSV file
    output_file <- file.path("outputs", paste0(assay_name, "_export.txt"))
    write.table(export_data, output_file, row.names = FALSE, sep = "\t", quote = F)
}

# Export all assays
export_all_assays <- function(qf) {
    # Get the names of all assays
    # assay_names <- names(assays(qf))
    assay_names <- c("peptides", "peptides_norm", "peptides_log", "proteins", "proteins_norm", "proteins_imptd")
    dir.create("outputs")
    # Export each assay
    for (assay_name in assay_names) {
        export_assay_with_metadata(qf, assay_name)
    }
}

# Plot the QC boxplots
create_boxplots <- function(scp, i, is_log2, name) {
    sce <- scp[[i]]
    assay_data <- as.data.frame(SummarizedExperiment::assay(sce)) |>
        tibble::rownames_to_column("FeatureID")
    col_data <- as.data.frame(SummarizedExperiment::colData(scp)) |>
        tibble::rownames_to_column("SampleID")
    long_data <- assay_data |>
        tidyr::pivot_longer(
            cols = -FeatureID,
            names_to = "SampleID",
            values_to = "Value"
        )
    long_data <- long_data |>
        dplyr::left_join(col_data, by = "SampleID")
    if (is_log2 == TRUE) {
        long_data$Value <- log2(long_data$Value)
    }
    long_data |>
        dplyr::filter(Value != "NaN") |>
        ggplot2::ggplot(ggplot2::aes(x = runCol, y = Value, fill = SampleType)) +
        ggplot2::geom_boxplot() +
        ggplot2::theme_bw() +
        ggplot2::labs(
            title = name,
            x = "Run",
            y = "Log2 intensity"
        ) +
        ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
}

# Heatmap
plot_heatmap <- function(scp, i) {
    sce <- scp[[i]]
    heatmap_mat <- as.matrix(SummarizedExperiment::assay(sce))
    heatmap_mat[is.na(heatmap_mat)] <- 0
    heatmap_bin <- ifelse(heatmap_mat > 0, 1, 0)
    colnames(heatmap_bin) <- gsub("Reporter.intensity.", "", colnames(heatmap_bin))
    heatmap(heatmap_bin, scale = "none", col = c("white", "black"), labRow = FALSE, margins = c(10, 5), cexCol = 0.5)
}
