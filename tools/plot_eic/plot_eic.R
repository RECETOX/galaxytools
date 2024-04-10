# Load the required package
library(xcms)

#' @param file_path A string specifying the path to the mzML file.
#' @return An MSnExp object containing the data from the mzML file.
read_data <- function(file_path) {
  data <- readMSData(files = file_path, mode = "onDisk")
  return(data)
}

#' @param data An MSnExp object containing the data from an mzML file.
#' @param mz_value A numeric value specifying the m/z value.
#' @param tolerance_ppm A numeric value specifying the tolerance in ppm.
#' @return A Chromatogram object containing the EIC.
extract_eic <- function(data, mz_value, tolerance_ppm) {
  tolerance <- mz_value * tolerance_ppm / 1e6
  eic <- chromatogram(data, mz = mz_value + c(-tolerance, tolerance), msLevel = 2)
  return(eic[[1]])
}

#' @param chrom A Chromatogram object.
#' @return A list containing the retention times and intensity values.
extract_rt_and_intensities <- function(chrom) {
  rt <- rtime(chrom)
  intensities <- intensity(chrom)
  return(list(rt = rt, intensities = intensities))
}

#' @param rt A numeric vector of retention times.
#' @param intensities A numeric vector of intensity values.
#' @param output_file A string specifying the output file name.
plot_eic <- function(rt, intensities, output_file) {
  png(filename = output_file)
  plot(rt, intensities, type = "p", xlab = "Retention Time (s)", ylab = "Intensity", main = "Extracted Ion Chromatogram")
  dev.off()
}

#' @param args A list of command line arguments.
main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  
  file_path <- args[1]
  mz_value <- as.numeric(args[2])
  tolerance_ppm <- as.numeric(args[3])
  output_file <- "plot_output.png"
  
  data <- read_data(file_path)
  chrom <- extract_eic(data, mz_value, tolerance_ppm)
  rt_and_intensities <- extract_rt_and_intensities(chrom)
  
  plot_eic(rt_and_intensities$rt, rt_and_intensities$intensities, output_file)
}

# Get the command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Call the main function
main()