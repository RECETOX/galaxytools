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
    data <- read.csv(data, header = TRUE, row.names = "sample_name")
    data <- preprocess_data(data)

    # remove blanks from dataset
    if (exclude_blanks) {
        data <- exclude_group(data)
    }

    # separate data into features, batch and group
    features <- data[, -c(1:4)]
    group <- as.numeric(data$class)
    batch <- data$batch

    # run WaveICA
    normalized_data <- WaveICA::WaveICA(
        data = features,
        wf = get_wf(wavelet_filter, wavelet_length),
        batch = batch,
        group = group,
        K = k,
        t = t,
        t2 = t2,
        alpha = alpha
        )

    return(normalized_data)
}


# Sort data, set numerical values for groups
preprocess_data <- function(data) {
    data <- data[order(data$injectionOrder, decreasing = FALSE), ] # sort data by injection order

    data$class[data$class == "blank"] <- 0
    data$class[data$class == "sample"] <- 1
    data$class[data$class == "QC"] <- 2

    return(data)
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
exclude_group <- function(data) {
    row_idx_to_exclude <- which(data$class %in% 0)
    if (length(row_idx_to_exclude) > 1) {
        data_without_blanks <- data[-c(row_idx_to_exclude), ]
        msg <- paste("Blank samples have been excluded from the dataframe.\n")
        cat(msg)
        return(data_without_blanks)
        }
    else {
        return(data)
    }
}


# Store output of WaveICA in a tsv file
store_data <- function(normalized_data, output) {
    write.table(normalized_data, file = output, sep = "\t", col.names = NA)
    cat("Normalization has been completed.\n")
}
