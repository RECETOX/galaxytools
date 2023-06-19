library(recetox.xmsannotator)

create_filter_by_adducts <- function(comma_separated_values) {
    if (comma_separated_values == "None") {
        return(NA)
    }
    filter_by <- strsplit(trimws(comma_separated_values), ",")[[1]]
    return(filter_by)
}

create_peak_table <- function(metadata_table, intensity_table) {
    metadata <- arrow::read_parquet(metadata_table) %>% select(id, mz, rt)
    intensity <- arrow::read_parquet(intensity_table)
    
    peak_table <- inner_join(metadata, intensity, by = "id")
    peak_table <- rename(peak_table, peak = id)
    return(peak_table)
}
