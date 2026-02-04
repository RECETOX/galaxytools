# Load libraries
library(mzR)
library(dplyr)
library(purrr)
library(tibble)
library(ggplot2)
library(readr)
library(optparse)

# Parse command line arguments
option_list <- list(
  make_option(c("--markers"), type = "character", default = NULL,
              help = "Path to markers TSV file (formula, mz, rt columns)", metavar = "FILE"),
  make_option(c("--mzml"), type = "character", default = NULL,
              help = "Path to input mzML file", metavar = "FILE"),
  make_option(c("--scans-output"), type = "character", default = NULL,
              help = "Path to output TSV file for extracted scans", metavar = "FILE"),
  make_option(c("--fits-output"), type = "character", default = NULL,
              help = "Path to output TSV file for Gaussian fits", metavar = "FILE"),
  make_option(c("--plots-output"), type = "character", default = NULL,
              help = "Path to output PDF file for plots (optional)", metavar = "FILE"),
  make_option(c("--rt-range"), type = "double", default = 12,
              help = "RT window range in seconds [default %default]", metavar = "NUMBER"),
  make_option(c("--no-plot"), action = "store_true", default = FALSE,
              help = "Disable plotting even if --plots-output is specified")
)

opt_parser <- OptionParser(
  option_list = option_list,
  description = "Target screening workflow: extract chromatographic peaks from mzML data"
)
opt <- parse_args(opt_parser)

# Validate required arguments
if (is.null(opt$markers) || is.null(opt$mzml) || 
    is.null(opt$`scans-output`) || is.null(opt$`fits-output`)) {
  print_help(opt_parser)
  quit(status = 1)
}

# Extract parameters
markers_file <- opt$markers
mzml_file <- opt$mzml
scans_output <- opt$`scans-output`
fits_output <- opt$`fits-output`
plots_output <- opt$`plots-output`
rt_range <- opt$`rt-range`
do_plot <- !opt$`no-plot` && !is.null(plots_output)

# Helper functions
ppm_diff <- function(measured_mz, theoretical_mz) {
  abs((measured_mz - theoretical_mz) / theoretical_mz) * 1e6
}

gaussian_model <- function(params, rt, intensity) {
  amplitude <- params[1]
  mean <- params[2]
  sd <- params[3]
  pred <- amplitude * exp(-0.5 * ((rt - mean) / sd)^2)
  sum((intensity - pred)^2)
}

process_suspect <- function(mz, rt, suspect_idx, header, rt_range, ms_data) {
  rt_min <- rt - rt_range
  rt_max <- rt + rt_range
  scan_indices <- which(header$retentionTime >= rt_min & header$retentionTime <= rt_max)
  
  if (length(scan_indices) == 0) {
    message(paste("No scans found for suspect", suspect_idx, "(mz =", mz, ", rt =", rt, ")"))
    return(NULL)
  }
  
  map_dfr(scan_indices, function(scan_idx) {
    peaks_data <- peaks(ms_data, scan_idx)
    if (is.null(peaks_data) || nrow(peaks_data) == 0) {
      return(NULL)
    }
    
    mz_values <- peaks_data[, 1]
    closest_idx <- which.min(abs(mz_values - mz))
    closest_mz <- mz_values[closest_idx]
    closest_intensity <- peaks_data[closest_idx, 2]
    
    tibble(
      suspect_idx = suspect_idx,
      suspect_mz = mz,
      suspect_rt = rt,
      scan_idx = scan_idx,
      scan_rt = header$retentionTime[scan_idx],
      matched_mz = closest_mz,
      matched_intensity = closest_intensity,
      ppm_error = ppm_diff(closest_mz, mz)
    )
  })
}

fit_gaussian <- function(df) {
  rt_values <- df$scan_rt
  intensity_values <- df$matched_intensity
  
  initial_amplitude <- max(intensity_values)
  initial_mean <- rt_values[which.max(intensity_values)]
  initial_sd <- max(diff(range(rt_values)) / 4, 1e-3)
  
  fit_result <- optim(
    c(initial_amplitude, initial_mean, initial_sd),
    gaussian_model,
    rt = rt_values,
    intensity = intensity_values,
    method = "Nelder-Mead"
  )
  
  if (fit_result$convergence != 0) {
    message(paste("Skipping suspect", df$suspect_idx[1], "(optim failed)"))
    return(NULL)
  }
  
  fitted_amplitude <- fit_result$par[1]
  fitted_mean <- fit_result$par[2]
  fitted_sd <- fit_result$par[3]
  
  if (fitted_sd <= 0) {
    message(paste("Skipping suspect", df$suspect_idx[1], "(non-positive SD)"))
    return(NULL)
  }
  
  fitted_curve <- fitted_amplitude * exp(-0.5 * ((rt_values - fitted_mean) / fitted_sd)^2)
  rmse_norm <- sqrt(mean((intensity_values - fitted_curve)^2)) / max(intensity_values)
  error_threshold <- 0.25
  if (rmse_norm > error_threshold) {
    message(paste("Skipping suspect", df$suspect_idx[1], "(norm RMSE =", round(rmse_norm, 3), ")"))
    return(NULL)
  }
  
  tibble(
    suspect_idx = df$suspect_idx[1],
    suspect_mz = df$suspect_mz[1],
    suspect_rt = df$suspect_rt[1],
    fitted_amplitude = fitted_amplitude,
    fitted_mean = fitted_mean,
    fitted_sd = fitted_sd,
    num_scans = nrow(df),
    fit_rmse_norm = rmse_norm
  )
}

plot_gaussian <- function(df, fit_row, rt_range) {
  rt_values <- df$scan_rt
  intensity_values <- df$matched_intensity
  
  fitted_amplitude <- fit_row$fitted_amplitude
  fitted_mean <- fit_row$fitted_mean
  fitted_sd <- fit_row$fitted_sd
  
  rt_window_min <- df$suspect_rt[1] - rt_range
  rt_window_max <- df$suspect_rt[1] + rt_range
  rt_smooth <- seq(rt_window_min, rt_window_max, length.out = 200)
  intensity_smooth <- fitted_amplitude * exp(-0.5 * ((rt_smooth - fitted_mean) / fitted_sd)^2)
  
  plot_df <- tibble(rt = rt_values, intensity = intensity_values)
  smooth_df <- tibble(rt = rt_smooth, intensity = intensity_smooth)
  
  apex_y <- max(intensity_values)
  min_y <- min(intensity_values)
  label_text <- paste0(
    "Amp: ", round(fitted_amplitude, 2),
    "\nMean RT: ", round(fitted_mean, 2),
    "\nSD: ", round(fitted_sd, 3)
  )
  
  p <- ggplot(plot_df, aes(x = rt, y = intensity)) +
    geom_point(color = "#1f77b4", size = 2) +
    geom_line(data = smooth_df, aes(x = rt, y = intensity), color = "#d62728", linewidth = 1) +
    annotate(
      "text",
      x = df$suspect_rt[1],
      y = min_y + 0.05 * (apex_y - min_y),
      label = label_text,
      hjust = 0,
      vjust = 0,
      size = 3.5
    ) +
    labs(
      title = paste0("Gaussian Peak Fit - Suspect ", df$suspect_idx[1],
                     " (mz = ", round(df$suspect_mz[1], 3), ")"),
      x = "Retention Time (s)",
      y = "Intensity"
    ) +
    coord_cartesian(xlim = c(rt_window_min, rt_window_max)) +
    theme_minimal(base_size = 12)
  
  print(p)
}

# Main function
main <- function() {
  # Read markers table
  suspect_tbl <- read_tsv(markers_file, show_col_types = FALSE) %>%
    as_tibble() %>%
    mutate(suspect_idx = row_number())
  
  # Read the mzML file
  ms_data <- openMSfile(mzml_file)
  header <- header(ms_data)
  
  # Process all suspects
  results_df <- suspect_tbl %>%
    select(mz, rt, suspect_idx) %>%
    pmap_dfr(~process_suspect(mz = ..1, rt = ..2, suspect_idx = ..3, header = header, 
                               rt_range = rt_range, ms_data = ms_data))
  
  # Write scans output
  write.table(results_df, scans_output, sep = "\t", row.names = FALSE, quote = FALSE)
  
  # Fit Gaussian peaks
  gaussian_fits_df <- results_df %>%
    group_by(suspect_idx, suspect_mz, suspect_rt) %>%
    group_split() %>%
    map_dfr(fit_gaussian, .id = "fit_id")
  
  # Write fits output
  if (nrow(gaussian_fits_df) == 0) {
    message("No Gaussian fits passed the quality criteria.")
    write.table(data.frame(), fits_output, sep = "\t", row.names = FALSE, quote = FALSE)
  } else {
    write.table(gaussian_fits_df, fits_output, sep = "\t", row.names = FALSE, quote = FALSE)
  }
  
  # Generate plots if requested
  if (do_plot && nrow(gaussian_fits_df) > 0) {
    pdf(plots_output, width = 10, height = 7)
    suspect_groups <- results_df %>%
      group_by(suspect_idx, suspect_mz, suspect_rt) %>%
      group_split()
    
    for (i in seq_len(nrow(gaussian_fits_df))) {
      fit_row <- gaussian_fits_df[i, ]
      g <- suspect_groups[[i]]
      plot_gaussian(g, fit_row, rt_range)
    }
    dev.off()
  }
  
  close(ms_data)
}

# Run main function
main()