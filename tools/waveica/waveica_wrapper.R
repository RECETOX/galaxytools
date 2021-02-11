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

    norm_data <- WaveICA::WaveICA(
        data = features_data,
        wf = define_wt_function(wfil, wlen),
        batch = batch_data,
        group = group_data,
        K = K,
        t = t,
        t2 = t2,
        alpha = alpha
        )
        return(norm_data)
}


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

    list <- list(features_data, batch_data, group_data)
    return(list)
}


define_wt_function <- function(
    wfil,
    wlen
) {
    wf=paste(wfil,wlen,sep="")

    if (wf == "d2") {
        wf <- "haar" # exception to wavelet filter in R
    }
    
    return(wf)
}


store_data <- function(normalized_data, output) {
    normalized_data <- normalized_data$data_wave
    save(normalized_data,file=output)
    print("Tool successfully finished.")
}