library(recetox.xmsannotator)

read_peak_table <- function(peak_table) {
    peak_table = arrow::read_parquet(peak_table)

    if("peak" %in% colnames(peak_table)) {
        if (!is.integer(peak_table$peak)) {
            peak_table$peak <- as.integer(peak_table$peak)
        }
    }
    return(peak_table)
}

create_filter_by_adducts <- function(comma_separated_values) {
    if (comma_separated_values == "None") {
        return(NA)
    }
    filter_by <- strsplit(trimws(comma_separated_values), ",")[[1]]
    return(filter_by)
}
