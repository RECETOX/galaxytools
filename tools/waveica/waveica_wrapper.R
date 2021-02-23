waveica <- function(
    data,
    wavelet_filter,
    wavelet_length,
    K,
    t,
    t2,
    alpha,
    exclude_blanks
) {

    # get input from the Galaxy, preprocess data
    data <- read.csv(data, header = TRUE, row.names = "sample_name")
    data <- preprocess_data(data)

    # divide data into features, batch and group
    features <- data[,-c(1:4)]
    group <- as.numeric(data$class)
    batch <- data$batch

    # run WaveICA
    normalized_data <- WaveICA::WaveICA(
        data = features,
        wf = get_wf(wavelet_filter, wavelet_length),
        batch = batch,
        group = group,
        K = K,
        t = t,
        t2 = t2,
        alpha = alpha
        )
    
    # exclude blanks if selected by user
    if (exclude_blanks) {
        normalized_data$data_wave <- exclude_group(normalized_data, group)
    }

    return(normalized_data)
}


# Sort data, set numerical values for groups
preprocess_data <- function(data) {
    data <- data[order(data$injectionOrder, decreasing=FALSE),] # sort data by injection order

    data$class[data$class=="blank"] <- 0
    data$class[data$class=="sample"] <- 1
    data$class[data$class=="QC"] <- 2

    return(data)
}


# Create appropriate input for R wavelets function
get_wf <- function(wavelet_filter, wavelet_length) {
    
    wf=paste(wavelet_filter, wavelet_length, sep="")

    # exception to the wavelet function
    if (wf == "d2") {
        wf <- "haar"
        }
    
    return(wf)
}


# Exclude blanks from a dataframe (can be optimized to exclude other samples)
exclude_group <- function(features, group) {
    
    row_idx_to_exclude <- which(group %in% 0)
    features_no_blanks <- features$data_wave[-c(row_idx_to_exclude),]

    msg <- paste("Blank samples have been excluded from the dataframe.\n")
    cat(msg)

    return(features_no_blanks)
}


# Store output of WaveICA 
store_data <- function(normalized_data, output) {
    write.csv(normalized_data,file=output)
    cat("Normalization has been completed.\n")
}