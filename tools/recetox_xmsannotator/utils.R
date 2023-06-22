library(recetox.xmsannotator)
library(dplyr)

load_table <- function(filename, filetype) {
    if (filename == "None") {
        return(NULL)
    }
    if (filetype == "csv") {
        return(as.data.frame(read.csv(filename)))
    } else {
        return(as.data.frame(arrow::read_parquet(filename)))
    }
}

save_table <- function(table, filename, filetype) {
    if (filetype == "csv") {
        write.csv(table, filename, row.names = FALSE)
    } else {
        arrow::write_parquet(table, filename)
    }
}

create_filter_by_adducts <- function(comma_separated_values) {
    if (comma_separated_values == "None") {
        return(NA)
    }
    filter_by <- strsplit(trimws(comma_separated_values), ",")[[1]]
    return(filter_by)
}

create_peak_table <- function(metadata_table, intensity_table) {
    metadata_table <- select(metadata_table, id, mz, rt)
    peak_table <- inner_join(metadata_table, intensity_table, by = "id")
    peak_table <- rename(peak_table, peak = id)
    peak_table$peak <- as.integer(peak_table$peak)
    return(peak_table)
}
