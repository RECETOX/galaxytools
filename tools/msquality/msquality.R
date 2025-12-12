#!/usr/bin/env Rscript

# Suppress package startup messages
suppressPackageStartupMessages({
    library(MsQuality)
    library(Spectra)
    library(MzR)
})

# Function to read input file paths
read_input_files <- function(file_path) {
    lines <- readLines(file_path)
    # Remove empty lines
    lines <- lines[nchar(trimws(lines)) > 0]
    return(lines)
}

# Function to get metrics that don't require parameters
get_default_metrics <- function() {
    # List of metrics that don't require additional parameters
    # Based on MsQuality Bioconductor documentation
    # These are the most common quality metrics for MS data
    metrics <- c(
        "areaUnderTIC",
        "areaUnderTicRtQuantiles",
        "chromatographyDuration",
        "extentIdentifiedPrecursorIntensity",
        "medianPrecursorMz",
        "medianTicRtIwQuartiles",
        "msSignal10xChange",
        "numberSpectra",
        "rtDuration",
        "rtIqr",
        "rtIwq",
        "rtOverMsQuarters",
        "ticQuartiles"
    )
    return(metrics)
}

# Function to get MS2-specific metrics
get_ms2_metrics <- function() {
    metrics <- c(
        "numberMS2Spectra",
        "medianPrecursorIntensity",
        "medianNumberFragments"
    )
    return(metrics)
}

# Main execution
main <- function() {
    # Read command line arguments from Galaxy
    args <- commandArgs(trailingOnly = TRUE)
    
    # Parse arguments
    inputs_file <- NULL
    ms2_metrics_flag <- FALSE
    
    i <- 1
    while (i <= length(args)) {
        if (args[i] == "--inputs") {
            inputs_file <- args[i + 1]
            i <- i + 2
        } else if (args[i] == "--ms2_metrics") {
            ms2_metrics_flag <- (args[i + 1] == "TRUE")
            i <- i + 2
        } else {
            i <- i + 1
        }
    }
    
    # Get input file paths
    input_files <- read_input_files(inputs_file)
    
    cat("Processing", length(input_files), "file(s)\n")
    
    # Initialize results list
    all_results <- list()
    
    # Process each file
    for (i in seq_along(input_files)) {
        file_path <- input_files[i]
        file_name <- basename(file_path)
        
        cat("Processing file:", file_name, "\n")
        
        tryCatch({
            # Read the mzML file using Spectra
            # The Spectra function automatically detects mzML files and uses the appropriate backend
            sps <- Spectra(file_path)
            
            # Get metrics to calculate
            metrics_to_calculate <- character(0)
            
            # Add default metrics
            default_metrics <- get_default_metrics()
            metrics_to_calculate <- c(metrics_to_calculate, default_metrics)
            
            # Add MS2 metrics if requested
            if (ms2_metrics_flag) {
                ms2_metrics <- get_ms2_metrics()
                metrics_to_calculate <- c(metrics_to_calculate, ms2_metrics)
            }
            
            # Calculate quality metrics
            qc_result <- MsQuality::calculateMetrics(
                sps,
                metrics = metrics_to_calculate
            )
            
            # Store results with file name
            all_results[[file_name]] <- qc_result
            
        }, error = function(e) {
            cat("Error processing file", file_name, ":", conditionMessage(e), "\n")
        })
    }
    
    # Combine results into a table
    if (length(all_results) > 0) {
        # Convert to data frame
        result_df <- data.frame(Metric = names(all_results[[1]]))
        
        # Add columns for each sample
        for (sample_name in names(all_results)) {
            result_df[[sample_name]] <- all_results[[sample_name]]
        }
        
        # Write output table
        write.table(
            result_df,
            file = "output_table.tsv",
            sep = "\t",
            row.names = FALSE,
            quote = FALSE
        )
        
        cat("Successfully created quality metrics table\n")
    } else {
        cat("Warning: No results generated\n")
        # Create empty output
        write.table(
            data.frame(Metric = character(0)),
            file = "output_table.tsv",
            sep = "\t",
            row.names = FALSE,
            quote = FALSE
        )
    }
}

# Run main function
main()
