suppressPackageStartupMessages({
    library(Spectra)
    library(MsQuality)
})

# Build a Spectra object from the input files.
read_spectra <- function(input_files) {
    sps <- Spectra(unname(input_files), backend = MsBackendMzR())
    if (length(sps) == 0) {
        stop("No spectra could be read from the input files.")
    }
    sps
}

# Sample labels come from the element identifiers of the input collection, and
# those do not always carry the file extension: it depends on how the files were
# uploaded. Drop a trailing raw data extension so that samples are named
# identically in the metrics table, the plots and the mzQC files, and so that mzQC
# files are named after the sample rather than after the file twice over.
sample_labels <- function(labels) {
    labels <- basename(labels)
    labels <- sub("\\.(mzML|mzXML)$", "", labels, ignore.case = TRUE)
    duplicated_labels <- unique(labels[duplicated(labels)])
    if (length(duplicated_labels) > 0) {
        stop(paste0(
            "Sample names collide once the file extensions are removed: ",
            paste(duplicated_labels, collapse = ", ")
        ))
    }
    labels
}

# Map every spectrum to the label of the file it came from.
#
# Spectra reports dataOrigin as the resolved path of the file, which follows
# symbolic links and ignores the name the file was linked to. The sample labels
# are therefore taken from the tool inputs and matched back to the spectra by
# resolved path, so that neither the Galaxy file names on disk nor the extension
# of the upload leak into the results.
resolve_groups <- function(sps, input_files) {
    resolved <- normalizePath(unname(input_files), winslash = "/", mustWork = TRUE)
    names(resolved) <- names(input_files)
    origin <- normalizePath(as.character(dataOrigin(sps)), winslash = "/", mustWork = TRUE)
    labels <- names(resolved)[match(origin, resolved)]
    if (anyNA(labels)) {
        stop(paste0(
            "Could not assign these files to an input sample: ",
            paste(unique(origin[is.na(labels)]), collapse = ", ")
        ))
    }
    labels
}

# Fail early with the list of usable metrics instead of failing deep inside a
# metric function. The available names change between Bioconductor releases,
# so they are validated against the installed package rather than a static list.
select_metrics <- function(sps, metrics) {
    available <- qualityMetrics(sps)
    if (is.null(metrics) || length(metrics) == 0) {
        return(available)
    }
    unknown <- setdiff(metrics, available)
    if (length(unknown) > 0) {
        stop(paste0(
            "Unknown metric(s): ", paste(unknown, collapse = ", "),
            ".\nAvailable metrics: ", paste(available, collapse = ", ")
        ))
    }
    metrics
}

write_metrics <- function(metrics_matrix, out_metrics) {
    metrics_table <- as.data.frame(metrics_matrix)
    metrics_table <- cbind(
        sample = rownames(metrics_table), metrics_table,
        row.names = NULL
    )
    write.table(
        metrics_table,
        file = out_metrics, sep = "\t",
        quote = FALSE, row.names = FALSE, na = ""
    )
}

# The metric matrix carries the PSI-MS accession of every metric as an
# attribute named after the metric function; turn those into a small table so
# the wide metric output can be read without looking every term up by hand.
# Metrics returning more than one value contribute one accession for several
# columns, named after the metric function rather than the column. Metrics
# without an accession in the installed MsQuality version are reported as blank.
write_legend <- function(metrics_matrix, metrics, out_legend) {
    accessions <- vapply(metrics, function(metric) {
        accession <- attr(metrics_matrix, metric)
        if (is.null(accession)) "" else accession
    }, character(1))
    legend <- data.frame(
        metric = metrics,
        accession = unname(accessions),
        stringsAsFactors = FALSE
    )
    write.table(
        legend,
        file = out_legend, sep = "\t",
        quote = FALSE, row.names = FALSE
    )
}

# plotMetric returns a plotly widget by default, which cannot be rasterised,
# so the ggplot object is requested explicitly.
write_plots <- function(metrics_matrix, metrics, plots_dir) {
    dir.create(plots_dir, showWarnings = FALSE, recursive = TRUE)
    for (metric in metrics) {
        plot <- plotMetric(qc = metrics_matrix, metric = metric, plotly = FALSE)
        ggplot2::ggsave(
            filename = file.path(plots_dir, paste0(metric, ".png")),
            plot = plot, width = 10, height = 6, dpi = 100
        )
    }
}

# MsQuality derives the mzQC input file name, location and file format from the
# grouping factor, which resolves to the path the dataset is stored under on the
# Galaxy side. Point all three at the actual input file instead, as a URI, which
# is what the mzQC specification asks for and what rmzqc refuses to write
# otherwise. The name is the one the input arrived under, as the storage path of
# a dataset is of no use to whoever reads the document later.
prepare_mzqc_document <- function(document, sample, input_file, file_format,
                                  display_name) {
    location <- rmzqc::localFileToURI(
        normalizePath(input_file, winslash = "/", mustWork = TRUE)
    )
    for (i in seq_along(document$runQualities)) {
        run <- document$runQualities[[i]]
        input_files <- run$metadata$inputFiles
        for (j in seq_along(input_files)) {
            input_files[[j]]$name <- display_name
            input_files[[j]]$location <- location
            input_files[[j]]$fileFormat <- file_format
        }
        run$metadata$inputFiles <- input_files
        run$metadata$label <- sample
        document$runQualities[[i]] <- run
    }
    document
}

# MsQuality writes the version of the rmzqc package into mzQC.version instead of
# the version of the mzQC specification the document conforms to.
fix_mzqc_version <- function(document, mzqc_version) {
    tryCatch(
        {
            rmzqc::MzQCmzQC$new(
                version = mzqc_version,
                creationDate = document$creationDate,
                contactName = "Galaxy",
                description = document$description,
                runQualities = document$runQualities,
                setQualities = document$setQualities,
                controlledVocabularies = document$controlledVocabularies
            )
        },
        error = function(e) {
            warning(paste0(
                "Could not set the mzQC version to ", mzqc_version,
                ", keeping the version reported by MsQuality: ", e$message
            ))
            document
        }
    )
}

# MsQuality returns one mzQC document per sample, so every sample is written as
# its own file and collected into a Galaxy list collection.
write_mzqc <- function(documents, input_files, display_names, mzqc_dir,
                       file_format, mzqc_version) {
    dir.create(mzqc_dir, showWarnings = FALSE, recursive = TRUE)
    written <- character(length(documents))
    for (i in seq_along(documents)) {
        sample <- basename(documents[[i]]$runQualities[[1]]$metadata$label)
        document <- documents[[i]]
        if (!sample %in% names(input_files)) {
            stop(paste0("No input file recorded for sample '", sample, "'."))
        }
        display_name <- if (sample %in% names(display_names)) {
            display_names[[sample]]
        } else {
            sample
        }
        document <- prepare_mzqc_document(
            document, sample, input_files[[sample]], file_format, display_name
        )
        document <- fix_mzqc_version(document, mzqc_version)
        # writeMZQC refuses any name that does not end in ".mzQC".
        path <- file.path(mzqc_dir, paste0(sample, ".mzQC"))
        rmzqc::writeMZQC(path, document)
        written[i] <- path
    }
    written
}

# input_files must be a named character vector, names being the names the inputs
# arrived under and values the paths of the input files. The names are reported
# back, without a trailing raw data extension, see sample_labels().
run_msquality <- function(input_files, metrics = NULL,
                          out_metrics = NULL, out_legend = NULL,
                          mzqc_dir = NULL, plots_dir = NULL,
                          ms_level = 1L, filter_empty = FALSE,
                          cores = 1, mzqc_version = "1.0.0",
                          file_format = "MS:1000584") {
    if (is.null(names(input_files)) || any(names(input_files) == "")) {
        stop("'input_files' must be a named vector of sample labels to file paths.")
    }
    # The names as they arrived are kept for the mzQC documents, the names used
    # throughout the analysis have the file extension removed.
    labels <- sample_labels(names(input_files))
    display_names <- stats::setNames(names(input_files), labels)
    names(input_files) <- labels
    sps <- read_spectra(input_files)
    metrics <- select_metrics(sps, metrics)
    bpparam <- if (cores > 1) {
        BiocParallel::MulticoreParam(workers = cores)
    } else {
        BiocParallel::SerialParam()
    }
    groups <- resolve_groups(sps, input_files)

    # MsQuality only produces mzQC documents from a fresh calculation, so the
    # metrics are calculated once for the table and the plots and once more for
    # mzQC. Neither is calculated twice when only one of the two is asked for.
    if (!is.null(out_metrics) || !is.null(plots_dir)) {
        metrics_matrix <- calculateMetricsFromSpectra(
            spectra = sps, metrics = metrics,
            filterEmptySpectra = filter_empty, f = groups,
            format = "data.frame", msLevel = ms_level,
            BPPARAM = bpparam
        )
        if (!is.null(out_metrics)) {
            write_metrics(metrics_matrix, out_metrics)
            write_legend(metrics_matrix, metrics, out_legend)
        }
        if (!is.null(plots_dir)) {
            write_plots(metrics_matrix, metrics, plots_dir)
        }
    }

    if (!is.null(mzqc_dir)) {
        documents <- calculateMetricsFromSpectra(
            spectra = sps, metrics = metrics,
            filterEmptySpectra = filter_empty, f = groups,
            format = "mzQC", msLevel = ms_level,
            BPPARAM = bpparam
        )
        file_format <- rmzqc::getCVTemplate(accession = file_format)
        write_mzqc(
            documents, input_files, display_names,
            mzqc_dir, file_format, mzqc_version
        )
    }

    invisible(TRUE)
}
