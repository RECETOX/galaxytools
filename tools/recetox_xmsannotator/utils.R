library(recetox.xmsannotator)
library(dplyr)

load_adduct_table <- function(filename) {
    if (filename == "None") {
        return(NULL)
    }
    return(load_adduct_table_parquet(filename))
}

load_compound_table <- function(filename) {
    if (filename == "None") {
        return(NULL)
    }
    return(load_compound_table_parquet(filename))
}

load_table <- function(filename) {
    if (filename == "None") {
        return(NULL)
    }
    return(as.data.frame(arrow::read_parquet(filename)))
}

create_filter_by_adducts <- function(comma_separated_values) {
    if (comma_separated_values == "None") {
        return(NA)
    }
    filter_by <- strsplit(trimws(comma_separated_values), ",")[[1]]
    return(filter_by)
}

create_peak_table <- function(metadata_table, intensity_table) {
    metadata_table <- load_table(metadata_table) %>% select(id, mz, rt)
    intensity_table <- load_table(intensity_table)
    peak_table <- inner_join(metadata_table, intensity_table, by = "id")
    peak_table <- rename(peak_table, peak = id)
    peak_table$peak <- as.integer(peak_table$peak)
    return(peak_table)
}
