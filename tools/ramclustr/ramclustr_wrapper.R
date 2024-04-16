store_output <- function(ramclustr_obj,
                         output_merge_msp,
                         output_spec_abundance,
                         msp_file) {
  RAMClustR::write.msp(ramclustr_obj, one.file = output_merge_msp)
  write.table(ramclustr_obj$SpecAbund,
    file = output_spec_abundance,
    row.names = TRUE, quote = FALSE, col.names = NA, sep = "\t"
  )

  if (!is.null(msp_file)) {
    exp_name <- ramclustr_obj$ExpDes[[1]][which(
      row.names(ramclustr_obj$ExpDes[[1]]) == "Experiment"
    ), 1]
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

read_ramclustr_aplcms <- function(ms1_featuredefinitions = NULL,
                                  ms1_featurevalues = NULL,
                                  df_phenodata = NULL,
                                  phenodata_ext = NULL,
                                  exp_des = NULL,
                                  st = NULL,
                                  ensure_no_na = TRUE) {
  ms1_featuredefinitions <- arrow::read_parquet(ms1_featuredefinitions)
  ms1_featurevalues <- arrow::read_parquet(ms1_featurevalues)

  if (!is.null(df_phenodata)) {
    if (phenodata_ext == "csv") {
      df_phenodata <- read.csv(
        file = df_phenodata,
        header = TRUE, check.names = FALSE
      )
    } else {
      df_phenodata <- read.csv(
        file = df_phenodata,
        header = TRUE, check.names = FALSE, sep = "\t"
      )
    }
  }
  if (!is.null(exp_des)) {
    exp_des <- load_experiment_definition(exp_des)
  }

  feature_values <- ms1_featurevalues[-1]
  feature_values <- t(feature_values)
  colnames(feature_values) <- ms1_featurevalues[[1]]

  feature_definitions <- data.frame(ms1_featuredefinitions)

  ramclustr_obj <- RAMClustR::rc.get.df.data(
    ms1_featureDefinitions = feature_definitions,
    ms1_featureValues = feature_values,
    phenoData = df_phenodata,
    ExpDes = exp_des,
    st = st,
    ensure.no.na = ensure_no_na
  )
  return(ramclustr_obj)
}

apply_normalisation <- function(ramclustr_obj = NULL,
                                normalize_method,
                                metadata_file = NULL,
                                qc_inj_range,
                                p_cut,
                                rsq_cut,
                                p_adjust) {
  batch <- NULL
  order <- NULL
  qc <- NULL

  if (normalize_method == "TIC") {
    ramclustr_obj <- RAMClustR::rc.feature.normalize.tic(
      ramclustObj =
        ramclustr_obj
    )
  } else if (normalize_method == "quantile") {
    ramclustr_obj <- RAMClustR::rc.feature.normalize.quantile(ramclustr_obj)
  } else if (normalize_method == "batch.qc") {
    if (!(is.null(metadata_file) || metadata_file == "None")) {
      metadata <- read_metadata(metadata_file)
      batch <- metadata$batch
      order <- metadata$order
      qc <- metadata$qc
    }

    ramclustr_obj <- RAMClustR::rc.feature.normalize.batch.qc(
      order = order,
      batch = batch,
      qc = qc,
      ramclustObj = ramclustr_obj,
      qc.inj.range = qc_inj_range
    )
  } else {
    if (!(is.null(metadata_file) || metadata_file == "None")) {
      metadata <- read_metadata(metadata_file)
      batch <- metadata$batch
      order <- metadata$order
      qc <- metadata$qc
    }

    ramclustr_obj <- RAMClustR::rc.feature.normalize.qc(
      order = order,
      batch = batch,
      qc = qc,
      ramclustObj = ramclustr_obj,
      p.cut = p_cut,
      rsq.cut = rsq_cut,
      p.adjust = p_adjust
    )
  }
  return(ramclustr_obj)
}
