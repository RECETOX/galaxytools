library(enviPat)
library(Spectra)
library(MsBackendMsp)
library(MetaboCoreUtils)
library(readr)
library(tidyselect)
library(stringr)
library(dplyr)

isotopes <- data.frame(
    element = character(),
    abundance = numeric(),
    isotope = character()
)
element <- character()
abundance <- numeric()
adducts <- data.frame(
    Name = character(),
    Mult = numeric(),
    Formula_add = character(),
    Formula_ded = character(),
    Charge = numeric(),
    Ion_mode = character(),
    Mass = numeric()
)
mz <- numeric()
peaks <- numeric()
isos <- character()
retention_time <- numeric()
full_formula <- character()
name <- character()


parse_args <- function() {
    args <- commandArgs(trailingOnly = TRUE)

    compound_table_full <- read_tsv(
        file = args[1],
        col_types = cols(
            name = col_character(),
            formula = col_character(),
            rt = col_double(),
            .default = col_guess()
        )
    )

    # Extract selected columns
    compound_table <- compound_table_full[, intersect(c("name", "formula", "rt"), colnames(compound_table_full)), drop = FALSE]

    # Extract remaining columns
    remaining_columns <- setdiff(colnames(compound_table_full), colnames(compound_table))
    remaining_data <- compound_table_full[, c("name", remaining_columns), drop = FALSE]

    # Handle missing or empty rel_to argument
    rel_to_value <- if (length(args) >= 8 && args[8] != "") {
        if (args[8] == "none") 0 else as.numeric(args[8])
    } else {
        0 # Default value is 0
    }

    if (!rel_to_value %in% c(0, 1, 2, 3, 4)) {
        stop(
            "Invalid value for rel_to. Expected 'none' (0),",
            " or a numeric value between 0 and 4."
        )
    }

    parsed <- list(
        compound_table = compound_table,
        adducts_to_use = c(unlist(strsplit(args[2], ",", fixed = TRUE))),
        threshold = as.numeric(args[3]),
        append_adducts = args[4],
        append_isotopes = args[5],
        out_format = args[6],
        outfile = args[7],
        rel_to = rel_to_value,
        remaining_data = remaining_data
    )
    parsed
}

generate_isotope_spectra <- function(compound_table,
                                     adducts_to_use,
                                     append_adducts,
                                     threshold,
                                     rel_to) {
    data(isotopes)
    data(adducts)

    # Add custom adducts for positive ion mode that don't already exist in enviPat
    # Based on enviPat adduct table format with all 9 columns:
    # Name, calc, Charge, Mult, Mass, Ion_mode, Formula_add, Formula_ded, Multi
    # Note: M+, M+Na, M+NH4 already exist in enviPat, so we only add M2+ and M-H+
    custom_adducts <- data.frame(
        Name = c("M2+", "M-H+"),
        calc = c("M/2-0.00054858", "M-1.007825"),
        Charge = c(2, 1),
        Mult = c(1, 1),
        Mass = c(-0.00054858, -1.007825),
        Ion_mode = c("positive", "positive"),
        Formula_add = c("FALSE", "FALSE"),
        Formula_ded = c("FALSE", "H1"),
        Multi = c(1, 1),
        stringsAsFactors = FALSE
    )
    
    # Merge custom adducts with the enviPat adducts
    adducts <- rbind(adducts, custom_adducts)

    monoisotopic <- isotopes |>
        dplyr::group_by(element) |>
        dplyr::slice_max(abundance, n = 1) |>
        dplyr::filter(!stringr::str_detect(element, "\\[|\\]"))

    chemforms <- enviPat::check_chemform(isotopes, compound_table$formula)[, 2]
    spectra <- data.frame()

    for (current in adducts_to_use) {
        adduct <- adducts[adducts$Name == current, ]
        multiplied_chemforms <- enviPat::multiform(chemforms, adduct$Mult)

        if (adduct$Ion_mode == "negative") {
            merged_chemforms <- enviPat::subform(
                multiplied_chemforms,
                adduct$Formula_ded
            )
        } else {
            merged_chemforms <- enviPat::mergeform(
                multiplied_chemforms,
                adduct$Formula_add
            )
        }

        charge_string <- paste0(
            if (adduct$Charge > 0) "+" else "-",
            if (abs(adduct$Charge) > 1) abs(adduct$Charge) else ""
        )
        adduct_string <- paste0("[", adduct$Name, "]", charge_string)
        precursor_mass <- MetaboCoreUtils::calculateMass(multiplied_chemforms)
        precursor_mz <- precursor_mass + adduct$Mass

        if (append_adducts == TRUE) {
            names <- paste(
                compound_table$name,
                paste0("(", adduct$Name, ")"),
                sep = " "
            )
        } else {
            names <- compound_table$name
        }

        spectra_df <- data.frame(
            name = names,
            adduct = adduct_string,
            formula = chemforms,
            charge = adduct$Charge,
            ionization_mode = adduct$Ion_mode,
            precursor_mz = precursor_mz,
            msLevel = as.integer(1)
        )

        if ("rt" %in% colnames(compound_table)) {
            spectra_df$retention_time <- compound_table$rt
        }

        patterns <- enviPat::isopattern(
            isotopes = isotopes,
            chemforms = merged_chemforms,
            charge = adduct$Charge,
            threshold = threshold,
            rel_to = rel_to,
        )

        mzs <- list()
        intensities <- list()
        isos <- list()

        for (i in seq_along(patterns)) {
            mzs <- append(mzs, list(patterns[[i]][, 1]))
            intensities <- append(intensities, list(patterns[[i]][, 2]))

            # select all columns which describe the elemental composition
            # remove all 12C, 35Cl etc.
            # remove isotopes which don't occur
            compositions <- as.data.frame(patterns[[i]][, -c(1, 2), drop = FALSE]) |>
                dplyr::select(-tidyselect::any_of(monoisotopic$isotope)) |>
                dplyr::select_if(~ !all(. == 0))

            # combine elemental composition into single string
            compositions <- compositions |>
                dplyr::rowwise() |>
                dplyr::mutate(isotopes = paste(
                    purrr::map2_chr(
                        names(compositions),
                        dplyr::c_across(everything()),
                        ~ paste(.x, .y, sep = ":")
                    ),
                    collapse = ", "
                )) |>
                dplyr::ungroup() |>
                dplyr::select(isotopes)
            isos <- append(isos, list(compositions$isotopes))
        }

        spectra_df$mz <- mzs
        spectra_df$intensity <- intensities
        spectra_df$isotopes <- isos
        spectra <- rbind(spectra, spectra_df)
    }
    spectra
}

join_remaining_data <- function(df, remaining_data) {
    if (nrow(remaining_data) > 0) {
        df <- df %>%
            dplyr::mutate(base_name = stringr::str_trim(stringr::str_remove(name, "\\s*\\([^)]*\\)$")))
        df <- dplyr::left_join(df, remaining_data, by = c("base_name" = "name"))
        df <- df %>% dplyr::select(-base_name)
    }
    df
}

write_to_msp <- function(spectra, file, remaining_data) {
    spectra <- join_remaining_data(spectra, remaining_data)
    sps <- Spectra::Spectra(dplyr::select(spectra, -isotopes))
    Spectra::export(sps, MsBackendMsp::MsBackendMsp(), file = file)
}

write_to_table <- function(spectra, file, append_isotopes, remaining_data) {
    entries <- spectra |>
        dplyr::rowwise() |>
        dplyr::mutate(peaks = paste(unlist(mz), collapse = ";")) |>
        dplyr::mutate(isos = paste(unlist(isotopes), collapse = ";"))
    result <- tidyr::separate_longer_delim(
        entries,
        all_of(c("peaks", "isos")),
        ";"
    )
    result <- result |>
        dplyr::select(-c("mz", "intensity", "isotopes")) |>
        dplyr::rename(mz = peaks, isotopes = isos, rt = retention_time)

    if (append_isotopes) {
        result <- result |>
            dplyr::mutate(result,
                full_formula = ifelse(
                    is.na(isotopes) | isotopes == "",
                    formula,
                    paste0(formula, " (", isotopes, ")")
                )
            ) |>
            dplyr::select(-all_of(c("formula", "isotopes"))) |>
            dplyr::rename(formula = full_formula) |>
            dplyr::relocate(formula, .after = name)
    }
    result <- join_remaining_data(result, remaining_data)
    readr::write_tsv(result, file = file)
}

main <- function() {
    args <- parse_args()
    spectra <- generate_isotope_spectra(
        args$compound_table,
        args$adducts_to_use,
        args$append_adducts,
        args$threshold,
        args$rel_to
    )

    if (args$out_format == "msp") {
        write_to_msp(spectra, args$outfile, args$remaining_data)
    } else if (args$out_format == "tabular") {
        write_to_table(spectra, args$outfile, args$append_isotopes, args$remaining_data)
    }
}

# Call the main function
main()
