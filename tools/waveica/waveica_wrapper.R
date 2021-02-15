waveica <- function(
    data,
    wfil,
    wlen,
    batch,
    group,
    K,
    t,
    t2,
    alpha,
    group_label
) {

    # get input from the Galaxy
    input <- assign_data(data, batch, group)
    features_data <- input[[1]]
    batch_data <- input[[2]]
    group_data <- input[[3]]

    # run WaveICA
    normalized_data <- WaveICA::WaveICA(
        data = features_data,
        wf = define_wt_function(wfil, wlen),
        batch = batch_data,
        group = group_data,
        K = K,
        t = t,
        t2 = t2,
        alpha = alpha
        )
    
    # get spectra from the list of 1 item
    normalized_data <- normalized_data$data_wave

    # exclude a group if label is provided
    if (!is.null(group_label)) {
        normalized_data <- exclude_group(normalized_data, group_data, group_label)
    }

    return(normalized_data)
}


# This is not ideal since R will store 2 copies of each dataset. Will fix that once we use other input than Rdata
assign_data <- function(data, batch, group) {
    assign('features_data', get(load(data)))
    assign('batch_data', get(load(batch)))
    
    # handle optional "Group" input
    if (!is.null(group)) {
        assign('group_data', get(load(group)))
    } else {
        group_data <- NULL
    }

    input_data <- list(features_data, batch_data, group_data)
    return(input_data)
}


# Create appropriate input for R wavelets function
define_wt_function <- function(wfil, wlen) {
    
    wf=paste(wfil,wlen,sep="")

    # exception to the wavelet function
    if (wf == "d2") {
        wf <- "haar"
    }
    
    return(wf)
}


# Exclude certain group (e.g. blank) from a dataframe
exclude_group <- function(normalized_data, group_data, group_label) {
        
    if (is.null(group_data)) {
        cat("Cannot exclude a group as no group data was provided.\n")
    }
    else {
        idx_to_exclude <- which(group_data %in% group_label)
        data_without_group <- normalized_data[-c(idx_to_exclude),]

        msg <- paste("Group with label", group_label, "has been excluded from the dataframe.\n")
        cat(msg)

        return(data_without_group)
    }
}


# Store output of WaveICA 
store_data <- function(normalized_data, output) {
    save(normalized_data,file=output)
    cat("Normalization has been completed.\n")
}