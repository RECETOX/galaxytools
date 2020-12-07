store_output <- function(
    ramclustr_obj,
    output_filename,
    output_method_metadata,
    output_merge_msp,
    output_spec_abundance)
{
    save(ramclustr_obj, file = output_filename)
    RAMClustR::write.methods(ramclustr_obj, output_method_metadata)
    RAMClustR::write.msp(ramclustr_obj, one.file = output_merge_msp)
    write.csv(ramclustr_obj$SpecAbund, file=output_spec_abundance, row.names=TRUE)
}

ramclustr_xcms <- function(
    input_xcms,
    st = NULL,
    maxt = NULL,
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
    fftempdir = NULL,
    replace_zeros
) 
{
    obj <- load(input_xcms)

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
        replace.zeros = replace_zeros
        )
        return (x)
}