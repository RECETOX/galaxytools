library(recetox.aplcms)

save_extracted_features <- function (df, filename) {
  columns <- c('mz', 'pos', 'sd1', 'sd2', 'area')
  arrow::write_parquet(df[columns], filename)
}

save_feature_sample_table <- function (df, filename) {
  columns <- c('feature', 'mz', 'rt', 'sample', 'sample_rt', 'sample_intensity')
  arrow::write_parquet(df[columns], filename)
}

known_table_columns <- function () {
  c('chemical_formula', 'HMDB_ID', 'KEGG_compound_ID', 'mass', 'ion.type',
    'm.z', 'Number_profiles_processed', 'Percent_found', 'mz_min', 'mz_max',
    'RT_mean', 'RT_sd', 'RT_min', 'RT_max', 'int_mean(log)', 'int_sd(log)',
    'int_min(log)', 'int_max(log)')
}

save_known_table <- function (df, filename) {
  columns <- known_table_columns()
  arrow::write_parquet(df[columns], filename)
}

read_known_table <- function (filename) {
  arrow::read_parquet(filename, col_select = known_table_columns())
}

save_pairing <- function(df, filename) {
  write.table(df, filename, row.names = FALSE, col.names = c('new', 'old'))
}

save_extracted_features_as_collection <- function (dfs, filenames) {
  filenames <- tools::file_path_sans_ext(filenames)
  filenames <- paste0('extracted-', filenames, '.parquet')
  mapply(save_extracted_features, dfs, filenames)
}

save_corrected_features_as_collection <- function (dfs, filenames) {
  filenames <- tools::file_path_sans_ext(filenames)
  filenames <- paste0('corrected-', filenames, '.parquet')
  mapply(save_extracted_features, dfs, filenames)
}

unsupervised_main <- function (sample_files, aligned_file, recovered_file, ...) {
  sample_files <- sort_samples_by_acquisition_number(sample_files)

  res <- unsupervised(filenames = sample_files, ...)

  save_extracted_features_as_collection(res$extracted_features, sample_files)
  save_corrected_features_as_collection(res$corrected_features, sample_files)

  save_feature_sample_table(res$aligned_feature_sample_table, aligned_file)
  save_feature_sample_table(res$recovered_feature_sample_table, recovered_file)
}

hybrid_main <- function (sample_files, known_table_file, updated_known_table_file, pairing_file, aligned_file, recovered_file, ...) {
  sample_files <- sort_samples_by_acquisition_number(sample_files)

  known <- read_known_table(known_table_file)
  res <- hybrid(filenames = sample_files, known_table = known, ...)

  save_known_table(res$updated_known_table, updated_known_table_file)
  save_pairing(res$features_known_table_pairing, pairing_file)

  save_extracted_features_as_collection(res$extracted_features, sample_files)
  save_corrected_features_as_collection(res$corrected_features, sample_files)

  save_feature_sample_table(res$aligned_feature_sample_table, aligned_file)
  save_feature_sample_table(res$recovered_feature_sample_table, recovered_file)
}
