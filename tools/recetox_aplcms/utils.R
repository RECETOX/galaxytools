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
  colnames(data) <- c("mz", "rt", "mz_min", "mz_max", sample_names)
  rownames(data) <- feature_names
  as.data.frame(data)
}

as_feature_sample_table <- function(rt_crosstab, int_crosstab) {
  feature_names <- rownames(rt_crosstab)
  sample_names <- colnames(rt_crosstab)[- (1:4)]

  feature_table <- data.frame(
    feature = feature_names,
    mz = rt_crosstab[, 1],
    rt = rt_crosstab[, 2]
  )

  # series of conversions to produce a table type from data.frame
  rt_crosstab <- as.table(as.matrix(rt_crosstab[, - (1:4)]))
  int_crosstab <- as.table(as.matrix(int_crosstab[, - (1:4)]))

  crosstab_axes <- list(feature = feature_names, sample = sample_names)
  dimnames(rt_crosstab) <- dimnames(int_crosstab) <- crosstab_axes

  x <- as.data.frame(rt_crosstab, responseName = "sample_rt")
  y <- as.data.frame(int_crosstab, responseName = "sample_intensity")

  data <- merge(x, y, by = c("feature", "sample"))
  data <- merge(feature_table, data, by = "feature")
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
  for (i in 0:(length(data) - 1)) {
    filename <- file.path(subdir, paste0(subdir, "_features_", i, ".parquet"))
    arrow::write_parquet(as.data.frame(data[i + 1]), filename)
  }
}

save_aligned_features <- function(aligned, rt_file, int_file, tol_file) {
  arrow::write_parquet(as.data.frame(aligned$rt_crosstab), rt_file)
  arrow::write_parquet(as.data.frame(aligned$int_crosstab), int_file)

  mz_tolerance <- c(aligned$mz_tolerance)
  rt_tolerance <- c(aligned$rt_tolerance)
  arrow::write_parquet(data.frame(mz_tolerance, rt_tolerance), tol_file)
}

load_aligned_features <- function(rt_file, int_file, tol_file) {
  rt_cross_table <- arrow::read_parquet(rt_file)
  int_cross_table <- arrow::read_parquet(int_file)
  tolerances_table <- arrow::read_parquet(tol_file)

  result <- list()
  result$mz_tolerance <- tolerances_table$mz_tolerance
  result$rt_tolerance <- tolerances_table$rt_tolerance
  result$rt_crosstab <- rt_cross_table
  result$int_crosstab <- int_cross_table
  return(result)
}

recover_signals <- function(cluster,
                            filenames,
                            extracted,
                            corrected,
                            aligned,
                            mz_tol = 1e-05,
                            mz_range = NA,
                            rt_range = NA,
                            use_observed_range = TRUE,
                            min_bandwidth = NA,
                            max_bandwidth = NA,
                            recover_min_count = 3) {
  if (!is(cluster, "cluster")) {
    cluster <- parallel::makeCluster(cluster)
    on.exit(parallel::stopCluster(cluster))
  }

  clusterExport(cluster, c("extracted", "corrected", "aligned", "recover.weaker"))
  clusterEvalQ(cluster, library("splines"))

  recovered <- parLapply(cluster, seq_along(filenames), function(i) {
    recover.weaker(
      loc = i,
      filename = filenames[[i]],
      this.f1 = extracted[[i]],
      this.f2 = corrected[[i]],
      pk.times = aligned$rt_crosstab,
      aligned.ftrs = aligned$int_crosstab,
      orig.tol = mz_tol,
      align.mz.tol = aligned$mz_tolerance,
      align.chr.tol = aligned$rt_tolerance,
      mz.range = mz_range,
      chr.range = rt_range,
      use.observed.range = use_observed_range,
      bandwidth = 0.5,
      min.bw = min_bandwidth,
      max.bw = max_bandwidth,
      recover.min.count = recover_min_count
    )
  })

  feature_table <- aligned$rt_crosstab[, 1:4]
  rt_crosstab <- cbind(feature_table, sapply(recovered, function(x) x$this.times))
  int_crosstab <- cbind(feature_table, sapply(recovered, function(x) x$this.ftrs))

  feature_names <- rownames(feature_table)
  sample_names <- colnames(aligned$rt_crosstab[, - (1:4)])

  list(
    extracted_features = lapply(recovered, function(x) x$this.f1),
    corrected_features = lapply(recovered, function(x) x$this.f2),
    rt_crosstab = as_feature_crosstab(feature_names, sample_names, rt_crosstab),
    int_crosstab = as_feature_crosstab(feature_names, sample_names, int_crosstab)
  )
}

create_feature_sample_table <- function(features) {
  table <- as_feature_sample_table(
      rt_crosstab = features$rt_crosstab,
      int_crosstab = features$int_crosstab
  )
  return(table)
}

known_table_columns <- function() {
  c("chemical_formula", "HMDB_ID", "KEGG_compound_ID", "mass", "ion.type",
    "m.z", "Number_profiles_processed", "Percent_found", "mz_min", "mz_max",
    "RT_mean", "RT_sd", "RT_min", "RT_max", "int_mean(log)", "int_sd(log)",
    "int_min(log)", "int_max(log)")
}

save_known_table <- function(df, filename) {
  columns <- known_table_columns()
  arrow::write_parquet(df[columns], filename)
}

read_known_table <- function(filename) {
  arrow::read_parquet(filename, col_select = known_table_columns())
}
