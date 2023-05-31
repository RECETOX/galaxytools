store_output <- function(ramclustr_obj,
                         output_merge_msp,
                         output_spec_abundance,
                         msp_file) {
    RAMClustR::write.msp(ramclustr_obj, one.file = output_merge_msp)
    write.csv(ramclustr_obj$SpecAbund, file = output_spec_abundance, row.names = TRUE, quote = FALSE)

    if (!is.null(msp_file)) {
        exp_name <- ramclustr_obj$ExpDes[[1]][which(row.names(ramclustr_obj$ExpDes[[1]]) == "Experiment"), 1]
        filename <- paste("spectra/", exp_name, ".msp", sep = "")
        file.copy(from = filename, to = msp_file, overwrite = TRUE)
    }
}

load_experiment_definition <- function(filename) {
    experiment <- RAMClustR::defineExperiment(csv = filename)
    return(experiment)
}

read_metadata <- function(filename) {
    data <- read.csv(filename, header = TRUE, stringsAsFactors = FALSE)

    if (!"qc" %in% colnames(data)) {
        if ("sampleType" %in% colnames(data)) {
            data$qc <- ifelse(data$sampleType == "qc", TRUE, FALSE)
        }
    }

    if (!"order" %in% colnames(data)) {
        if ("injectionOrder" %in% colnames(data)) {
            names(data)[names(data) == "injectionOrder"] <- "order"
        }
    }

    return(data)
}

read_ramclustr_aplcms <- function(ms1_featureDefinitions = NULL,
                                  ms1_featureValues = NULL,
                                  df_phenoData = NULL,
                                  ExpDes = NULL,
                                  st = NULL,
                                  ensure.no.na = TRUE) {
    ms1_featureDefinitions <- arrow::read_parquet(ms1_featureDefinitions)
    ms1_featureValues <- arrow::read_parquet(ms1_featureValues)

    if (!is.null(df_phenoData)) {
        df_phenoData <- arrow::read_parquet(df_phenoData)
    }
    if (!is.null(ExpDes)) {
        ExpDes <- load_experiment_definition(ExpDes)
    }

    featureValues <- ms1_featureValues[-1]
    featureValues <- t(featureValues)
    colnames(featureValues) <- ms1_featureValues[[1]]

    featureDefinitions <- data.frame(ms1_featureDefinitions)

    ramclustObj <- RAMClustR::rc.get.df.data(
        ms1_featureDefinitions = featureDefinitions,
        ms1_featureValues = featureValues,
        phenoData = df_phenoData,
        ExpDes = ExpDes,
        st = st,
        ensure.no.na = ensure.no.na
    )
    return(ramclustObj)
}

apply_normalisation <- function(ramclustObj = NULL,
                                normalize_method,
                                metadata_file = NULL,
                                qc_inj_range) {
    if (normalize_method == "TIC") {
        ramclustObj <- RAMClustR::rc.feature.normalize.tic(ramclustObj = ramclustObj)
    } else if (normalize_method == "quantile") {
        ramclustObj <- RAMClustR::rc.feature.normalize.quantile(ramclustObj)
    } else {
        batch <- NULL
        order <- NULL
        qc <- NULL

        if (!is.null(metadata_file)) {
            metadata <- read_metadata(metadata_file)
            batch <- metadata$batch
            order <- metadata$order
            qc <- metadata$qc
        }

        ramclustObj <- RAMClustR::rc.feature.normalize.batch.qc(
            order = order,
            batch = batch,
            qc = qc,
            ramclustObj = ramclustObj,
            qc.inj.range = qc_inj_range
        )
    }
    return(ramclustObj)
}
