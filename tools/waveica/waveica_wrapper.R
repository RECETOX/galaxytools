read_file <- function(file, metadata, ft_ext, mt_ext, transpose) {
    data <- read_data(file, ft_ext)

    if (transpose) {
        col_names <- c("sampleName", data[[1]])
        data <- tranpose_data(data, col_names)
    }

    if (!is.na(metadata)) {
        mt_data <- read_data(metadata, mt_ext)
        data <- merge(mt_data, data, by = "sampleName")
    }

    return(data)
}

read_data <- function(file, ext) {
    if (ext == "csv") {
        data <- read.csv(file, header = TRUE)
    } else if (ext == "tsv") {
        data <- read.csv(file, header = TRUE, sep = "\t")
    } else {
        data <- arrow::read_parquet(file)
    }

    return(data)
}

waveica <- function(file,
                    metadata = NA,
                    ext,
                    transpose = FALSE,
                    wavelet_filter,
                    wavelet_length,
                    k,
                    t,
                    t2,
                    alpha,
                    exclude_blanks) {
    # get input from the Galaxy, preprocess data
    ext <- strsplit(x = ext, split = "\\,")[[1]]

    ft_ext <- ext[1]
    mt_ext <- ext[2]

    data <- read_file(file, metadata, ft_ext, mt_ext, transpose)

    required_columns <- c(
        "sampleName", "class", "sampleType",
        "injectionOrder", "batch"
    )
    data <- verify_input_dataframe(data, required_columns)

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
                                transpose = FALSE,
                                wavelet_filter,
                                wavelet_length,
                                k,
                                alpha,
                                cutoff,
                                exclude_blanks) {
    # get input from the Galaxy, preprocess data
    ext <- strsplit(x = ext, split = "\\,")[[1]]

    ft_ext <- ext[1]
    mt_ext <- ext[2]

    data <- read_file(file, metadata, ft_ext, mt_ext, transpose)

    required_columns <- c("sampleName", "class", "sampleType", "injectionOrder")
    optional_columns <- c("batch")

    data <- verify_input_dataframe(data, required_columns)

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
    group <- enumerate_groups(as.character(data$sampleType))
    # remove blanks from dataset
    if (exclude_blanks) {
        data <- exclude_group(data, group)
    }

    return(data)
}

sort_by_injection_order <- function(data) {
    if ("batch" %in% colnames(data)) {
        data <- data[order(data[, "batch"], data[, "injectionOrder"], decreasing = FALSE), ]
    } else {
        data <- data[order(data[, "injectionOrder"], decreasing = FALSE), ]
    }
    return(data)
}

verify_input_dataframe <- function(data, required_columns) {
    if (anyNA(data)) {
        stop("Error: dataframe cannot contain NULL values!
Make sure that your dataframe does not contain empty cells")
    } else if (!all(required_columns %in% colnames(data))) {
        stop(
            "Error: missing metadata!
Make sure that the following columns are present in your dataframe: ",
            paste(required_columns, collapse = ", ")
        )
    }

    data <- verify_column_types(data, required_columns)

    return(data)
}

verify_column_types <- function(data, required_columns) {
    # Specify the column names and their expected types
    column_types <- list(
        "sampleName" = c("character", "factor"),
        "class" = c("character", "factor", "integer"),
        "sampleType" = c("character", "factor"),
        "injectionOrder" = "integer",
        "batch" = "integer"
    )

    column_types <- column_types[required_columns]

    for (col_name in names(data)) {
        actual_type <- class(data[[col_name]])
        if (col_name %in% names(column_types)) {
            expected_types <- column_types[[col_name]]

            if (!actual_type %in% expected_types) {
                stop(
                    "Column ", col_name, " is of type ", actual_type,
                    " but expected type is ",
                    paste(expected_types, collapse = " or "), "\n"
                )
            }
        } else {
            if (actual_type != "numeric") {
                data[[col_name]] <- as.numeric(as.character(data[[col_name]]))
            }
        }
    }
    return(data)
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

store_data <- function(data, feature_output, metadata_output, ext, split_output = FALSE) {
    if (ext == "parquet") {
        if (split_output == TRUE) {
            split_df <- split_output(data)
            arrow::write_parquet(split_df$metadata, metadata_output)
            arrow::write_parquet(split_df$feature_table, feature_output)
        } else {
            arrow::write_parquet(data, feature_output)
        }
    } else {
        if (split_output == TRUE) {
            split_df <- split_output(data)
            write.table(split_df$metadata, file = metadata_output, sep = "\t",
                row.names = FALSE, quote = FALSE
            )
            write.table(split_df$feature_table, file = feature_output, sep = "\t",
                row.names = FALSE, quote = FALSE
            )
        } else {
            write.table(data, file = feature_output, sep = "\t",
                row.names = FALSE, quote = FALSE
            )
        }
    }
    cat("Normalization has been completed.\n")
}

split_output <- function(df) {
    required_columns_set1 <- c("sampleName", "class", "sampleType", "injectionOrder", "batch")
    required_columns_set2 <- c("sampleName", "class", "sampleType", "injectionOrder")

    if (all(required_columns_set1 %in% colnames(df))) {
        metadata_df <- df[, required_columns_set1, drop = FALSE]
        df <- df[, -c(2:5)]
    } else if (all(required_columns_set2 %in% colnames(df))) {
        metadata_df <- df[, required_columns_set2, drop = FALSE]
        df <- df[, -c(2:4)]
    } else {
        stop("Neither set of required columns is present in the dataframe.")
    }

    # Transpose the feature table
    col_names <- c("id", as.vector(df[[1]]))
    feature_table <- tranpose_data(df, col_names)

    return(list(metadata = metadata_df, feature_table = feature_table))
}

tranpose_data <- function(data, column_names) {
    t_data <- data[-1]
    t_data <- t(t_data)
    tranposed_data <- data.frame(rownames(t_data), t_data)
    colnames(tranposed_data) <- column_names

    return(tranposed_data)
}
