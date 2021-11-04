waveica <- function(
    data,
    wavelet_filter,
    wavelet_length,
    k,
    t,
    t2,
    alpha,
    exclude_blanks
) {

    # get input from the Galaxy, preprocess data
    data <- read.csv(data, header = TRUE)

    required_columns <- c("sampleName", "class", "sampleType", "injectionOrder", "batch")
    if (anyNA(data)) {
        stop("Error: dataframe cannot contain NULL values!
Make sure that your dataframe does not contain empty cells")
    }
    else if (!all(required_columns %in% colnames(data))) {
        stop("Error: missing metadata!
Make sure that the following columns are present in your dataframe: [sampleName, class, sampleType, injectionOrder, batch]")
    }

    # sort data by injection order
    data <- data[order(data$injectionOrder, decreasing = FALSE), ]

    # separate data into features, batch and group
    features <- data[, -c(1:5)]
    group <- enumerate_groups(data$sampleType)
    batch <- data$batch

    # run WaveICA
    features <- WaveICA::WaveICA(
        data = features,
        wf = get_wf(wavelet_filter, wavelet_length),
        batch = batch,
        group = group,
        K = k,
        t = t,
        t2 = t2,
        alpha = alpha
        )

    data[, -c(1:5)] <- features$data_wave

    # remove blanks from dataset
    if (exclude_blanks) {
        data <- exclude_group(data, group)
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
        }
    else {
        return(data)
    }
}


# Store output of WaveICA in a tsv file
store_data <- function(data, output) {
    write.table(data, file = output, sep = "\t", col.names = NA)
    cat("Normalization has been completed.\n")
}
