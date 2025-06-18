# Read data from a file in the specified format (csv, tsv/tabular, or parquet)
read_data <- function(file, ext, transpose = FALSE) {
  # Reads a data file based on its extension and returns a data frame.
  if (ext == "csv") {
    tryCatch(
      {
        data <- read.csv(file, header = TRUE)
      },
      error = function(e) {
        stop(
          "Failed to read as CSV. The file may not be a
          valid text file or may be corrupted: ",
          file, "\nError: ", e$message
        )
      }
    )
  } else if (ext == "tsv" || ext == "tabular") {
    tryCatch(
      {
        data <- read.csv(file, header = TRUE, sep = "\t")
      },
      error = function(e) {
        stop(
          "Failed to read as TSV/tabular.
        The file may not be a valid text file or may be corrupted: ",
          file, "\nError: ", e$message
        )
      }
    )
  } else if (ext == "parquet") {
    data <- arrow::read_parquet(file)
  } else {
    stop(paste("Unsupported file extension or format for reading:", ext))
  }

  original_first_colname <- colnames(data)[1]
  if (transpose) {
    col_names <- c("sampleName", data[[1]])
    data <- tranpose_data(data, col_names)
  }
  return(list(data = data, original_first_colname = original_first_colname))
}

# Main function for batchwise WaveICA normalization
waveica <- function(data_matrix_file,
                    sample_metadata_file,
                    ft_ext,
                    mt_ext,
                    wavelet_filter,
                    wavelet_length,
                    k,
                    t,
                    t2,
                    alpha,
                    exclude_blanks,
                    transpose = FALSE) {
  # Reads feature and metadata tables, merges them,
  # verifies columns, runs WaveICA, and returns normalized data.
  read_features_reponse <- read_data(
    data_matrix_file, ft_ext,
    transpose
  )
  features <- read_features_reponse$data
  original_first_colname <- read_features_reponse$original_first_colname

  read_metadata_response <- read_data(sample_metadata_file, mt_ext)
  metadata <- read_metadata_response$data

  required_columns <- c(
    "sampleName", "class", "sampleType",
    "injectionOrder", "batch"
  )

  metadata <- dplyr::select(metadata, required_columns)

  # Ensure both tables have a sampleName column
  if (!"sampleName" %in% colnames(features) || !"sampleName" %in% colnames(metadata)) { # nolint
    stop("Both feature and metadata tables must contain a 'sampleName' column.")
  }
  data <- merge(metadata, features, by = "sampleName")


  data <- verify_input_dataframe(data, required_columns)

  data <- sort_by_injection_order(data)

  # Separate features, batch, and group columns
  feature_columns <- colnames(data)[!colnames(data) %in% required_columns]
  features <- data[, feature_columns]
  group <- enumerate_groups(as.character(data$sampleType))
  batch <- data$batch

  # Check that wavelet level is not too high for the number of samples
  max_level <- floor(log2(nrow(features)))
  requested_level <- as.numeric(wavelet_length)
  if (requested_level > max_level) {
    stop(sprintf(
      "Wavelet length/level (%d) is too high for
      the number of samples (%d). Maximum allowed is %d.",
      requested_level, nrow(features), max_level
    ))
  }
  # Run WaveICA normalization
  features <- recetox.waveica::waveica(
    data = features,
    wf = get_wf(wavelet_filter, wavelet_length),
    batch = batch,
    group = group,
    K = k,
    t = t,
    t2 = t2,
    alpha = alpha
  )
  non_feature_columns <- setdiff(colnames(data), feature_columns)
  print(non_feature_columns)
  cat("Number of rows:", nrow(data), "\n")
  cat("Number of columns:", ncol(data), "\n")
  # Update the data frame with normalized features
  data[, feature_columns] <- features

  # Optionally remove blank samples
  if (exclude_blanks) {
    data <- exclude_group(data, group)
  }
  if (transpose) {
    data <- reverse_tranpose_data(data, non_feature_columns)
    colnames(data)[1] <- original_first_colname
  }
  data
}

# Main function for single-batch WaveICA normalization
waveica_singlebatch <- function(data_matrix_file,
                                sample_metadata_file,
                                ft_ext,
                                mt_ext,
                                wavelet_filter,
                                wavelet_length,
                                k,
                                alpha,
                                cutoff,
                                exclude_blanks,
                                transpose = FALSE) {
  # Reads feature and metadata tables, merges them,
  # verifies columns, runs WaveICA (single batch), and returns normalized data.
  read_features_reponse <- read_data(data_matrix_file, ft_ext, transpose)
  features <- read_features_reponse$data
  original_first_colname <- read_features_reponse$original_first_colname

  read_data_response <- read_data(sample_metadata_file, mt_ext)
  metadata <- read_data_response$data

  # Ensure both tables have a sampleName column
  if (!"sampleName" %in% colnames(features) ||
    !"sampleName" %in% colnames(metadata)) { # nolint
    stop("Both feature and metadata tables must contain a 'sampleName' column.")
  }
  data <- merge(metadata, features, by = "sampleName")

  required_columns <- c("sampleName", "class", "sampleType", "injectionOrder")
  optional_columns <- c("batch")
  data <- verify_input_dataframe(data, required_columns)

  data <- sort_by_injection_order(data)

  feature_columns <- colnames(data)[
    !colnames(data) %in% c(required_columns, optional_columns)
  ]
  features <- data[, feature_columns]
  injection_order <- data$injectionOrder

  # Run WaveICA normalization (single batch)
  features <- recetox.waveica::waveica_nonbatchwise(
    data = features,
    wf = get_wf(wavelet_filter, wavelet_length),
    injection_order = injection_order,
    K = k,
    alpha = alpha,
    cutoff = cutoff
  )
  non_feature_columns <- setdiff(colnames(data), feature_columns)
  print(non_feature_columns)
  cat("Number of rows:", nrow(data), "\n")
  cat("Number of columns:", ncol(data), "\n")
  # Update the data frame with normalized features
  data[, feature_columns] <- features
  group <- enumerate_groups(as.character(data$sampleType))
  # Optionally remove blank samples
  if (exclude_blanks) {
    data <- exclude_group(data, group)
  }
  if (transpose) {
    data <- reverse_tranpose_data(data, non_feature_columns)
    colnames(data)[1] <- original_first_colname
  }
  data
}

# Sorts the data frame by batch and injection order (if batch exists),
# otherwise by injection order only
sort_by_injection_order <- function(data) {
  if ("batch" %in% colnames(data)) {
    data <- data[
      order(data[, "batch"],
        data[, "injectionOrder"],
        decreasing = FALSE
      ),
    ]
  } else {
    data <- data[order(data[, "injectionOrder"], decreasing = FALSE), ]
  }
  data
}

# Verifies that required columns exist and that there are no missing values
verify_input_dataframe <- function(data, required_columns) {
  if (anyNA(data)) {
    stop("Error: dataframe cannot contain NULL values!
    \nMake sure that your dataframe does not contain empty cells")
  } else if (!all(required_columns %in% colnames(data))) {
    stop(
      "Error: missing metadata!
      \nMake sure that the following columns are present in your dataframe: ",
      paste(required_columns, collapse = ", ")
    )
  }
  data <- verify_column_types(data, required_columns)
  data
}

# Checks column types for required and feature columns
# and removes problematic feature columns
verify_column_types <- function(data, required_columns) {
  # Checks that required columns have the correct type
  # and removes non-numeric feature columns efficiently.
  column_types <- list(
    "sampleName" = c("character", "factor"),
    "class" = c("character", "factor", "integer"),
    "sampleType" = c("character", "factor"),
    "injectionOrder" = "integer",
    "batch" = "integer"
  )
  column_types <- column_types[required_columns]

  # Check required columns' types (fast, vectorized)
  for (col_name in names(column_types)) {
    if (!col_name %in% names(data)) next
    expected_types <- column_types[[col_name]]
    actual_type <- class(data[[col_name]])
    if (!actual_type %in% expected_types) {
      stop(
        "Column ", col_name, " is of type ", actual_type,
        " but expected type is ",
        paste(expected_types, collapse = " or "), "\n"
      )
    }
  }

  # Identify feature columns (not required columns)
  feature_cols <- setdiff(names(data), required_columns)
  # Try to convert all feature columns to numeric in one go
  # as well as suppressing warnings
  data[feature_cols] <- suppressWarnings(
    lapply(
      data[feature_cols],
      function(x) as.numeric(as.character(x))
    )
  )
  # Find columns that are problematic (contain any NA after conversion)
  na_counts <- vapply(data[feature_cols], function(x) any(is.na(x)), logical(1))
  removed_columns <- names(na_counts)[na_counts]
  if (length(removed_columns) > 0) {
    message(
      "Removed problematic columns (non-numeric): ",
      paste(removed_columns, collapse = ", ")
    )
  }

  # Keep only good columns
  keep_cols <- !(names(data) %in% removed_columns)
  data <- data[, keep_cols, drop = FALSE]
  data
}

# Enumerates group labels: blank=0, sample=1, qc=2, standard=3
enumerate_groups <- function(group) {
  group[grepl("blank", tolower(group))] <- 0
  group[grepl("sample", tolower(group))] <- 1
  group[grepl("qc", tolower(group))] <- 2
  group[grepl("standard", tolower(group))] <- 3
  group
}

# Returns the correct wavelet filter string for the R wavelets function
get_wf <- function(wavelet_filter, wavelet_length) {
  wf <- paste(wavelet_filter, wavelet_length, sep = "")
  # Exception for Daubechies-2
  if (wf == "d2") {
    wf <- "haar"
  }
  wf
}

# Removes blank samples (group==0) from the data frame
exclude_group <- function(data, group) {
  row_idx_to_exclude <- which(group %in% 0)
  if (length(row_idx_to_exclude) > 0) {
    data_without_blanks <- data[-c(row_idx_to_exclude), ]
    cat("Blank samples have been excluded from the dataframe.\n")
    data_without_blanks
  } else {
    data
  }
}

# Stores the output data in the requested format (csv, tsv/tabular, parquet),
# optionally splitting metadata and features
store_data <- function(data, feature_output, ext) {
  if (ext == "parquet") {
    arrow::write_parquet(data, feature_output)
  } else if (ext == "csv") {
    write.csv(data, file = feature_output, row.names = FALSE, quote = FALSE)
  } else if (ext == "tsv" || ext == "tabular") {
    write.table(data,
      file = feature_output, sep = "\t",
      row.names = FALSE, quote = FALSE
    )
  } else {
    stop(paste("Unsupported file extension:", ext))
  }
  cat("Normalization has been completed.\n")
}

tranpose_data <- function(data, column_names) {
  t_data <- data[-1]
  t_data <- t(t_data)
  tranposed_data <- data.frame(rownames(t_data), t_data)
  colnames(tranposed_data) <- column_names

  tranposed_data
}

reverse_tranpose_data <- function(data, non_feature_columns) {
  # Remove all columns that are in non_feature_columns, except the first column
  cols_to_keep <- !(colnames(data) %in% non_feature_columns)
  cols_to_keep[1] <- TRUE # Always keep the first column
  data <- data[, cols_to_keep, drop = FALSE]

  # Convert to character to avoid factors
  data[] <- lapply(data, as.character)
  # The first column becomes the new column names
  new_colnames <- as.character(data[[1]])
  # Remove the first column
  t_data <- data[, -1, drop = FALSE]
  # Transpose the rest
  t_data <- t(t_data)
  # Convert to data frame
  transposed <- as.data.frame(t_data, stringsAsFactors = FALSE)
  # The first row becomes the first column
  first_col <- rownames(transposed)
  transposed <- cbind(first_col, transposed)
  # Set column names
  colnames(transposed) <- c(colnames(data)[1], new_colnames)
  rownames(transposed) <- NULL
  transposed
}
