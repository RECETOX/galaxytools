waveica <- function(
    data,
    wfil,
    wlen,
    batch,
    group,
    K,
    t,
    t2,
    alpha
) {

    input <- assign_data(data, batch, group)
    features_data <- input[[1]]
    batch_data <- input[[2]]
    group_data <- input[[3]]

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
        return(normalized_data)
}


# This is not ideal since R stores 2 copies of each dataset. Will be able to fix that once we use other input than Rdata
assign_data <- function(
    data,
    batch,
    group
) {
    assign('features_data', get(load(data)))
    assign('batch_data', get(load(batch)))
    
    if (!is.null(group)) {
        assign('group_data', get(load(group)))
    } else {
        group_data <- NULL
    }

    input_data <- list(features_data, batch_data, group_data)
    return(input_data)
}


# Creates appropriate input for R wavelets function
define_wt_function <- function(
    wfil,
    wlen
) {
    wf=paste(wfil,wlen,sep="")

    if (wf == "d2") {
        wf <- "haar" # exception to wavelet function
    }
    
    return(wf)
}


# Stores output of WaveICA 
store_data <- function(normalized_data, output) {
    normalized_data <- normalized_data$data_wave
    save(normalized_data,file=output)
    print("Normalization has been completed.")
}