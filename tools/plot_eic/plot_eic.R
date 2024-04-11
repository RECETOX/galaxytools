#' @param file_path A string specifying the path to the mzML file.
#' @return An MSnExp object containing the data from the mzML file.
read_data <- function(file_path) {
  data <- MSnbase::readMSData(files = file_path, mode = "onDisk")
  return(data)
}

#' @param data An MSnExp object containing the data from an mzML file.
#' @param mz_value A numeric value specifying the m/z value.
#' @param tolerance_ppm A numeric value specifying the tolerance in ppm.
#' @return A Chromatogram object containing the EIC.
extract_eic <- function(data, mz_value, tolerance_ppm) {
  tolerance <- mz_value * tolerance_ppm / 1e6
  eic <- xcms::chromatogram(data, mz = mz_value + c(-tolerance, tolerance), msLevel = 2)
  return(eic[[1]])
}

#' @param chrom A Chromatogram object.
#' @return A list containing the retention times and intensity values.
extract_rt_and_intensities <- function(chrom) {
  rt <- xcms::rtime(chrom)
  intensities <- xcms::intensity(chrom)
  return(list(rt = rt, intensities = intensities))
}

#' @param rt A numeric vector of retention times.
#' @param intensities A numeric vector of intensity values.
#' @param output_file A string specifying the output file name.
#' @param mz_value A numeric value specifying the m/z value.
#' @param tolerance_ppm A numeric value specifying the tolerance in ppm.
plot_eic <- function(rt, intensities, output_file, mz_value, tolerance_ppm) {
  mz_min <- mz_value - tolerance_ppm / 1e6
  mz_max <- mz_value + tolerance_ppm / 1e6
  title <- paste("m/z range: [", mz_min, ", ", mz_max, "]", sep = "")
  
  png(filename = output_file)
  plot(rt, intensities, type = "l", xlab = "Retention Time (s)", ylab = "Intensity", main = title)
  dev.off()
}

#' @param args A list of command line arguments.
main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  
  file_path <- args[1]
  mz_value <- as.numeric(args[2])
  tolerance_ppm <- ifelse(length(args) >= 3, as.numeric(args[3]), 10)
  output_file <- "plot_output.png"
  print(tolerance_ppm)

  data <- read_data(file_path)
  chrom <- extract_eic(data, mz_value, tolerance_ppm)
  rt_and_intensities <- extract_rt_and_intensities(chrom)
  
  plot_eic(rt_and_intensities$rt, rt_and_intensities$intensities, output_file, mz_value, tolerance_ppm)
}

# Get the command line arguments
args <- commandArgs(trailingOnly = TRUE)
# Call the main function
main()