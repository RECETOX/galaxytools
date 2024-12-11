library(dplyr)
library(scp)

# GREP ONLY NAMES WITH _IMP, _NORM, _LOG, _BATCHC; don't report all datasets


# Function to export a single assay with metadata
export_assay_with_metadata <- function(qf, assay_name) {
  # Extract assay data, row metadata, and col metadata
  assay_data <- assay(qf[[assay_name]])
  row_metadata <- as.data.frame(rowData(qf[[assay_name]]))
  col_metadata <- as.data.frame(colData(qf))
  
  # Combine row metadata with assay data
  export_data <- cbind(RowNames = rownames(assay_data), row_metadata, as.data.frame(assay_data))
  
  # Save the table to a CSV file
  output_file <- paste0(assay_name, "_export.csv")
  write.csv(export_data, output_file, row.names = FALSE)
}

# Export all assays
export_all_assays <- function(qf) {
  # Get the names of all assays
  assay_names <- names(assays(qf))
  
  # Export each assay
  for (assay_name in assay_names) {
    export_assay_with_metadata(qf, assay_name)
  }
}