#' Read data from mzML file
#'
#' @param file_path Path to the mzML file
#' @return An OnDiskMSnExp object
read_data <- function(file_path) {
  data <- MSnbase::readMSData(files = file_path, mode = "onDisk")
  return(data)
}

#' Extract mz slice from data
#'
#' @param data An OnDiskMSnExp object
#' @param mz_value m/z value for the slice
#' @param tolerance_ppm Tolerance for m/z value in ppm
#' @return A Chromatogram object
extract_mz <- function(data, mz_value, tolerance_ppm) {
  tolerance <- mz_value * tolerance_ppm / 1e6
  extracted_mz <- xcms::chromatogram(data, mz = mz_value + c(-tolerance, tolerance), msLevel = 2)
  return(extracted_mz[[1]])
}

#' Extract retention times and intensities from chromatogram
#'
#' @param chrom A Chromatogram object
#' @return A list with retention times and intensities
extract_rt_and_intensities <- function(chrom) {
  rt <- xcms::rtime(chrom)
  intensities <- xcms::intensity(chrom)
  return(list(rt = rt, intensities = intensities))
}

#' Filter data by retention time
#'
#' @param data An OnDiskMSnExp object
#' @param rt Retention time for the slice
#' @param rt_range Retention time range for the slice
#' @return A Chromatogram object
filter_data_rt <- function(data, rt, rt_range) {
  rt_min <- rt - rt_range / 2
  rt_max <- rt + rt_range / 2
  filtered_data <- xcms::filterRt(data, c(rt_min, rt_max))
  return(filtered_data)
}

#' Plot data
#'
#' @param rt Vector of retention times
#' @param intensities Vector of intensities
#' @param output_file Path to the output file
#' @param mz_value m/z value for the slice
#' @param tolerance Tolerance for m/z value in ppm
plot_data <- function(rt, intensities, output_file, mz_value, tolerance) {
  mz_min <- mz_value - tolerance
  mz_max <- mz_value + tolerance
  title <- paste("m/z range: [", mz_min, ", ", mz_max, "]", sep = "")
  
  png(filename = output_file)
  plot(rt, intensities, type = "l", xlab = "Retention Time (s)", ylab = "Intensity", main = title)
  dev.off()
}

#' Main function
#'
#' @description This function reads the command line arguments, reads the mzML file, extracts the mz slice, 
#' filters the data by retention time, extracts the retention times and intensities, and plots the data.
main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  
  file_path <- args[1]
  mz_value <- as.numeric(args[2])
  tolerance_ppm <- ifelse(length(args) >= 4, as.numeric(args[3]), 10)
  rt <- ifelse(length(args) >= 4, as.numeric(args[4]), 0)
  rt_range <- ifelse(length(args) >= 5, as.numeric(args[5]), 5)
  output_file <- "plot_output.png"
  
  data <- read_data(file_path)
  
  # Extract mz first
  slice <- extract_mz(data, mz_value, tolerance_ppm)
  # Filter by retention time
  filtered_slice <- filter_data_rt(slice, rt, rt_range)
  rt_and_intensities <- extract_rt_and_intensities(filtered_slice)
  
  plot_data(rt_and_intensities$rt, rt_and_intensities$intensities, output_file, mz_value, tolerance_ppm)
}

# Get the command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Call the main function
main()