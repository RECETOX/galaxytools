read_csv <- function(file, metadata) {
  if (!is.na(metadata)) {
    ft_table <- read.csv(file, header = TRUE)
    mt_data <- read.csv(metadata, header = TRUE)
    data <- merge(mt_data, ft_table, by = "sampleName")
  } else {
    data <- read.csv(file, header = TRUE)
  }

  return(data)
}

read_tsv <- function(file, metadata) {
  if (!is.na(metadata)) {
    ft_table <- read.csv(file, header = TRUE, sep = "\t")
    mt_data <- read.csv(metadata, header = TRUE, sep = "\t")
    data <- merge(mt_data, ft_table, by = "sampleName")
  } else {
    data <- read.csv(file, header = TRUE, sep = "\t")
  }

  return(data)
}

read_parquet_file <- function(file, metadata) {
  if (!is.na(metadata)) {
    ft_table <- arrow::read_parquet(file)
    mt_data <- arrow::read_parquet(metadata)
    data <- merge(mt_data, ft_table, by = "sampleName")
  } else {
    data <- arrow::read_parquet(file)
  }

  return(data)
}

write_csv <- function(data, output) {
  write.csv(data, file = output, row.names = FALSE, quote = FALSE)
  cat("Normalization has been completed.\n")
}

write_tsv <- function(data, output) {
  write.table(data, file = output, sep = "\t", row.names = FALSE, quote = FALSE)
  cat("Normalization has been completed.\n")
}

write_parquet_file <- function(data, output) {
  arrow::write_parquet(data, sink = output)
  cat("Normalization has been completed.\n")
}

waveica <- function(file,
                    metadata = NA,
                    ext,
                    wavelet_filter,
                    wavelet_length,
                    k,
                    t,
                    t2,
                    alpha,
                    exclude_blanks) {

  # get input from the Galaxy, preprocess data

  if (ext == "csv") {
    data <- read_csv(file, metadata)
  } else if (ext == "tsv") {
    data <- read_tsv(file, metadata)
  } else {
    data <- read_parquet_file(file, metadata)
  }

  required_columns <- c("sampleName", "class", "sampleType", "injectionOrder", "batch")
  verify_input_dataframe(data, required_columns)

  data <- sort_by_injection_order(data)

  # separate data into features, batch and group
  feature_columns <- colnames(data)[!colnames(data) %in% required_columns]
  features <- data[, feature_columns]
  group <- enumerate_groups(as.character(data$sampleType))
  batch <- data$batch

  # run WaveICA
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

  data[, feature_columns] <- features

  # remove blanks from dataset
  if (exclude_blanks) {
    data <- exclude_group(data, group)
  }

  return(data)
}


waveica_singlebatch <- function(file,
                                metadata = NA,
                                ext,
                                wavelet_filter,
                                wavelet_length,
                                k,
                                alpha,
                                cutoff,
                                exclude_blanks) {

  # get input from the Galaxy, preprocess data
  if (ext == "csv") {
    data <- read_csv(file, metadata)
  } else if (ext == "tsv") {
    data <- read_tsv(file, metadata)
  } else {
    data <- read_parquet_file(file, metadata)
  }

  required_columns <- c("sampleName", "class", "sampleType", "injectionOrder")
  optional_columns <- c("batch")
  verify_input_dataframe(data, required_columns)

  data <- sort_by_injection_order(data)

  feature_columns <- colnames(data)[!colnames(data) %in% c(required_columns, optional_columns)]
  features <- data[, feature_columns]
  injection_order <- data$injectionOrder

  # run WaveICA
  features <- recetox.waveica::waveica_nonbatchwise(
    data = features,
    wf = get_wf(wavelet_filter, wavelet_length),
    injection_order = injection_order,
    K = k,
    alpha = alpha,
    cutoff = cutoff
  )

  data[, feature_columns] <- features

  # remove blanks from dataset
  if (exclude_blanks) {
    data <- exclude_group(data, group)
  }

  return(data)
}


sort_by_injection_order <- function(data) {
  if ("batch" %in% colnames(data)) {
    data <- data[order(data[, "batch"],
      data[, "injectionOrder"],
      decreasing = FALSE
    ), ]
  } else {
    data <- data[order(data[, "injectionOrder"],
      decreasing = FALSE
    ), ]
  }
  return(data)
}


verify_input_dataframe <- function(data, required_columns) {
  if (anyNA(data)) {
    stop("Error: dataframe cannot contain NULL values!
Make sure that your dataframe does not contain empty cells")
  } else if (!all(required_columns %in% colnames(data))) {
    stop("Error: missing metadata!
Make sure that the following columns are present in your dataframe: ", paste(required_columns, collapse = ", "))
  }
}


# Match group labels with [blank/sample/qc] and enumerate them
enumerate_groups <- function(group) {
  group[grepl("blank", tolower(group))] <- 0
  group[grepl("sample", tolower(group))] <- 1
  group[grepl("qc", tolower(group))] <- 2

  return(group)
}


# Create appropriate input for R wavelets function
get_wf <- function(wavelet_filter, wavelet_length) {
  wf <- paste(wavelet_filter, wavelet_length, sep = "")

  # exception to the wavelet function
  if (wf == "d2") {
    wf <- "haar"
  }

  return(wf)
}


# Exclude blanks from a dataframe
exclude_group <- function(data, group) {
  row_idx_to_exclude <- which(group %in% 0)
  if (length(row_idx_to_exclude) > 0) {
    data_without_blanks <- data[-c(row_idx_to_exclude), ]
    cat("Blank samples have been excluded from the dataframe.\n")
    return(data_without_blanks)
  } else {
    return(data)
  }
}


# Store output of WaveICA in a tsv file
store_data <- function(data, output, ext) {
  if (ext == "csv") {
    write_csv(data, output)
  } else if (ext == "tsv") {
    write_tsv(data, output)
  } else {
    write_parquet_file(data, output)
  }
}
