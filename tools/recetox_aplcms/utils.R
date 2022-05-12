library(recetox.aplcms)

align_features <- function(sample_names, ...) {
    aligned <- feature.align(...)
    feature_names <- seq_len(nrow(aligned$pk.times))

list(
    mz_tolerance = as.numeric(aligned$mz.tol),
    rt_tolerance = as.numeric(aligned$chr.tol),
    rt_crosstab = as_feature_crosstab(feature_names, sample_names, aligned$pk.times),
    int_crosstab = as_feature_crosstab(feature_names, sample_names, aligned$aligned.ftrs)
    )
}

get_sample_name <- function(filename) {
    tools::file_path_sans_ext(basename(filename))
}

as_feature_crosstab <- function(feature_names, sample_names, data) {
  colnames(data) <- c('mz', 'rt', 'mz_min', 'mz_max', sample_names)
  rownames(data) <- feature_names
  as.data.frame(data)
}

as_feature_sample_table <- function(rt_crosstab, int_crosstab) {
  feature_names <- rownames(rt_crosstab)
  sample_names <- colnames(rt_crosstab)[-(1:4)]

  feature_table <- data.frame(
    feature = feature_names,
    mz = rt_crosstab[, 1],
    rt = rt_crosstab[, 2]
  )

  # series of conversions to produce a table type from data.frame
  rt_crosstab <- as.table(as.matrix(rt_crosstab[, -(1:4)]))
  int_crosstab <- as.table(as.matrix(int_crosstab[, -(1:4)]))

  crosstab_axes <- list(feature = feature_names, sample = sample_names)
  dimnames(rt_crosstab) <- dimnames(int_crosstab) <- crosstab_axes

  x <- as.data.frame(rt_crosstab, responseName = 'sample_rt')
  y <- as.data.frame(int_crosstab, responseName = 'sample_intensity')

  data <- merge(x, y, by = c('feature', 'sample'))
  data <- merge(feature_table, data, by = 'feature')
  data
}

load_features <- function(files) {
    files_list <- sort_samples_by_acquisition_number(files)
    features <- lapply(files_list, arrow::read_parquet)
    features <- lapply(features, as.matrix)
    return(features)
}

save_data_as_parquet_files <- function(data, subdir) {
  dir.create(subdir)
  for (i in 0:(length(data)-1)) {
    filename <- file.path(subdir, paste0(subdir, "_features_", i, ".parquet"))
    arrow::write_parquet(as.data.frame(data[i+1]), filename)
  }
}

save_aligned_features <- function(aligned, rt_file, int_file, tol_file) {
  arrow::write_parquet(as.data.frame(aligned$rt_crosstab), rt_file)
  arrow::write_parquet(as.data.frame(aligned$int_crosstab), int_file)

  mz_tolerance <- c(aligned$mz_tolerance)
  rt_tolerance <- c(aligned$rt_tolerance)
  arrow::write_parquet(data.frame(mz_tolerance, rt_tolerance), tol_file)
}
