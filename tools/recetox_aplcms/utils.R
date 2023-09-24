library(recetox.aplcms)

get_env_sample_name < - function() {
  sample_name < -Sys.getenv("SAMPLE_NAME", unset = NA)
  if (nchar(sample_name) == 0) {
    sample_name < -NA
  }
  if (is.na(sample_name)) {
    message("The mzML file does not contain run ID.")
  }
  return(sample_name)
}

save_sample_name < - function(df, sample_name) {
  attr(df, "sample_name") < -sample_name
  return(df)
}

restore_sample_name < - function(df) {
  return(df$sample_id[1])
}

load_sample_name < - function(df) {
  sample_name < -attr(df, "sample_name")
  if (is.null(sample_name)) {
    return(NA)
  } else {
    return(sample_name)
  }
}

save_data_as_parquet_file < - function(data, filename) {
  arrow::write_parquet(data, filename)
}

load_data_from_parquet_file < - function(filename) {
  return(arrow::read_parquet(filename))
}

load_parquet_collection < - function(files) {
  features < -lapply(files, arrow::read_parquet)
  features < -lapply(features, tibble::as_tibble)
  return(features)
}

save_parquet_collection < - function(feature_tables, sample_names, subdir) {
  dir.create(subdir)
  for (i in seq_len(length(feature_tables))) {
    filename < -file.path(subdir, paste0(sample_names[i], ".parquet"))
    feature_table < -as.data.frame(feature_tables[[i]])
    feature_table < -save_sample_name(feature_table, sample_names[i])
    arrow::write_parquet(feature_table, filename)
  }
}

sort_by_sample_name < - function(tables, sample_names) {
  return(tables[order(sample_names)])
}

save_tolerances < - function(table, tol_file) {
  mz_tolerance < -c(table$mz_tol_relative)
  rt_tolerance < -c(table$rt_tol_relative)
  arrow::write_parquet(data.frame(mz_tolerance, rt_tolerance), tol_file)
}

save_aligned_features < - function(aligned_features, metadata_file, rt_file, intensity_file) {
  save_data_as_parquet_file(aligned_features$metadata, metadata_file)
  save_data_as_parquet_file(aligned_features$rt, rt_file)
  save_data_as_parquet_file(aligned_features$intensity, intensity_file)
}

select_table_with_sample_name < - function(tables, sample_name) {
  sample_names < -lapply(tables, load_sample_name)
  index < -which(sample_names == sample_name)
  if (length(index) > 0) {
    return(tables[[index]])
  } else {
    stop(sprintf("Mismatch - sample name '%s' not present in %s",
                 sample_name, paste(sample_names, collapse = ", ")))
  }
}

select_adjusted < - function(recovered_features) {
  return(recovered_features$adjusted_features)
}

known_table_columns < - function() {
  c("chemical_formula", "HMDB_ID", "KEGG_compound_ID", "mass", "ion.type",
    "m.z", "Number_profiles_processed", "Percent_found", "mz_min", "mz_max",
    "RT_mean", "RT_sd", "RT_min", "RT_max", "int_mean(log)", "int_sd(log)",
    "int_min(log)", "int_max(log)")
}

save_known_table < - function(table, filename) {
  columns < -known_table_columns()
  arrow::write_parquet(table$known_table[columns], filename)
}

read_known_table < - function(filename) {
  arrow::read_parquet(filename, col_select = known_table_columns())
}

save_pairing < - function(table, filename) {
  df < -table$pairing % > % as_tibble() % > % setNames(c("new", "old"))
  arrow::write_parquet(df, filename)
}

join_tables_to_list < - function(metadata, rt_table, intensity_table) {
  features < -new("list")
  features$metadata < -metadata
  features$intensity < -intensity_table
  features$rt < -rt_table
  return(features)
}

validate_sample_names < - function(sample_names) {
  if ((any(is.na(sample_names))) || (length(unique(sample_names)) != length(sample_names))) {
    stop(sprintf("Sample names absent or not unique - provided sample names: %s",
                 paste(sample_names, collapse = ", ")))
  }
}

determine_sigma_ratios < - function(sigma_ratio_lim_min = NA, sigma_ratio_lim_max = NA) {
  if (is.na(sigma_ratio_lim_min)) {
    sigma_ratio_lim_min < -0
  }
  if (is.na(sigma_ratio_lim_max)) {
    sigma_ratio_lim_max < -Inf
  }
  return(c(sigma_ratio_lim_min, sigma_ratio_lim_max))
}
