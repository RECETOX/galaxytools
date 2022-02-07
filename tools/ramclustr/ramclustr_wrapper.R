store_output <- function(
    ramclustr_obj,
    output_filename,
    output_method_metadata,
    output_merge_msp,
    output_spec_abundance) {
    save(ramclustr_obj, file = output_filename)
    RAMClustR::write.methods(ramclustr_obj, output_method_metadata)
    RAMClustR::write.msp(ramclustr_obj, one.file = output_merge_msp)
    write.csv(ramclustr_obj$SpecAbund, file = output_spec_abundance, row.names = TRUE)
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

ramclustr_xcms <- function(
    input_xcms,
    sr,
    deep_split,
    block_size,
    mult,
    hmax,
    collapse,
    use_pheno,
    qc_inj_range,
    normalize,
    min_module_size,
    linkage,
    mzdec,
    cor_method,
    rt_only_low_n,
    replace_zeros,
    st = NULL,
    maxt = NULL,
    fftempdir = NULL,
    metadata_file = NULL,
    exp_design = NULL
) {
    obj <- load(input_xcms)

    batch <- NULL
    order <- NULL
    qc <- NULL

    if (!is.null(metadata_file)) {
        metadata <- read_metadata(metadata_file)
        batch <- metadata$batch
        order <- metadata$order
        qc <- metadata$qc
    }

    experiment <- NULL

    if (!is.null(exp_design)) {
        experiment <- load_experiment_definition(exp_design)
    }

    x <- RAMClustR::ramclustR(
        xcmsObj = xdata,
        st = st,
        maxt = maxt,
        sr = sr,
        deepSplit = deep_split,
        blocksize = block_size,
        mult = mult,
        hmax = hmax,
        collapse = collapse,
        usePheno = use_pheno,
        mspout = FALSE,
        qc.inj.range = qc_inj_range,
        normalize = normalize,
        minModuleSize = min_module_size,
        linkage = linkage,
        mzdec = mzdec,
        cor.method = cor_method,
        rt.only.low.n = rt_only_low_n,
        fftempdir = fftempdir,
        replace.zeros = replace_zeros,
        batch = batch,
        order = order,
        qc = qc,
        ExpDes = experiment
        )
    return(x)
}

ramclustr_csv <- function(
    ms,
    idmsms,
    sample_name_column,
    feature_delimiter,
    retention_time_column,
    sr,
    deep_split,
    block_size,
    mult,
    hmax,
    collapse,
    qc_inj_range,
    normalize,
    min_module_size,
    linkage,
    mzdec,
    cor_method,
    rt_only_low_n,
    replace_zeros,
    st = NULL,
    maxt = NULL,
    fftempdir = NULL,
    metadata_file = NULL,
    exp_design = NULL
) {
    if (!file.exists(idmsms))
        idmsms <- NULL

    batch <- NULL
    order <- NULL
    qc <- NULL

    if (!is.null(metadata_file)) {
        metadata <- read_metadata(metadata_file)
        batch <- metadata$batch
        order <- metadata$order
        qc <- metadata$qc
    }

    experiment <- NULL

    if (!is.null(exp_design)) {
        experiment <- load_experiment_definition(exp_design)
    }

    x <- RAMClustR::ramclustR(
        ms = ms,
        idmsms = idmsms,
        featdelim = feature_delimiter,
        timepos = retention_time_column,
        sampNameCol = sample_name_column,
        st = st,
        maxt = maxt,
        sr = sr,
        deepSplit = deep_split,
        blocksize = block_size,
        mult = mult,
        hmax = hmax,
        collapse = collapse,
        mspout = FALSE,
        qc.inj.range = qc_inj_range,
        normalize = normalize,
        minModuleSize = min_module_size,
        linkage = linkage,
        mzdec = mzdec,
        cor.method = cor_method,
        rt.only.low.n = rt_only_low_n,
        fftempdir = fftempdir,
        replace.zeros = replace_zeros,
        batch = batch,
        order = order,
        qc = qc,
        ExpDes = experiment
        )
        return(x)
}
