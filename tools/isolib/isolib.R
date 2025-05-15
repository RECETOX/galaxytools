library(enviPat)
library(Spectra)
library(MsBackendMsp)
library(MetaboCoreUtils)
library(readr)
library(tidyselect)
library(dplyr)
library(stringr)
library(purrr)

# Declare global variables to suppress linter warnings
utils::globalVariables(c(
  "isotopes", "element", "abundance", "adducts", "mz", "peaks", "isos",
  "retention_time", "full_formula", "name"
))

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  compound_table <- read_tsv(
    file = args[1],
    col_types = "ccd",
    col_select = all_of(c("name", "formula")) | any_of("rt")
  )
  # Handle missing or empty rel_to argument
  rel_to_value <- if (length(args) >= 8 && args[8] != "") {
    if (args[8] == "none") 0 else as.numeric(args[8])
  } else {
    0 # Default value is 0
  }

  if (!rel_to_value %in% c(0, 1, 2, 3, 4)) {
    stop("Invalid value for rel_to. Expected 'none' (0),\
     or a numeric value between 0 and 4.")
  }

  parsed <- list(
    compound_table = compound_table,
    adducts_to_use = c(unlist(strsplit(args[2], ",", fixed = TRUE))),
    threshold = as.numeric(args[3]),
    append_adducts = args[4],
    append_isotopes = args[5],
    out_format = args[6],
    outfile = args[7],
    rel_to = rel_to_value
  )
  parsed
}

generate_isotope_spectra <- function(compound_table,
                                     adducts_to_use,
                                     append_adducts,
                                     threshold,
                                     rel_to) {
  data(isotopes, package = "enviPat") # Ensure isotopes data is loaded
  data(adducts, package = "enviPat") # Ensure adducts data is loaded

  monoisotopic <- isotopes |>
    dplyr::group_by(element) |>
    dplyr::slice_max(abundance, n = 1) |>
    dplyr::filter(!stringr::str_detect(element, "\\[|\\]"))

  chemforms <- check_chemform(isotopes, compound_table$formula)[, 2]
  spectra <- data.frame()

  for (current in adducts_to_use) {
    adduct <- adducts[adducts$Name == current, ]
    multiplied_chemforms <- multiform(chemforms, adduct$Mult)

    if (adduct$Ion_mode == "negative") {
      merged_chemforms <- subform(multiplied_chemforms, adduct$Formula_ded)
    } else {
      merged_chemforms <- mergeform(multiplied_chemforms, adduct$Formula_add)
    }

    charge_string <- paste0(
      if (adduct$Charge > 0) "+" else "-",
      if (abs(adduct$Charge) > 1) abs(adduct$Charge) else ""
    )
    adduct_string <- paste0("[", adduct$Name, "]", charge_string)
    precursor_mz <- calculateMass(multiplied_chemforms) + adduct$Mass

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
      rel_to = rel_to
    )

    mzs <- list()
    intensities <- list()
    isos <- list()

    for (i in seq_along(patterns)) {
      mzs <- append(mzs, list(patterns[[i]][, 1]))
      intensities <- append(intensities, list(patterns[[i]][, 2]))

      compositions <- as.data.frame(patterns[[i]][, -c(1, 2)]) |>
        dplyr::select(-tidyselect::any_of(monoisotopic$isotope)) |>
        dplyr::select_if(~ !all(. == 0))

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

write_to_msp <- function(spectra, file) {
  sps <- Spectra(dplyr::select(spectra, -isotopes))
  export(sps, MsBackendMsp(), file = file)
}

write_to_table <- function(spectra, file, append_isotopes) {
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
      dplyr::mutate(
        full_formula = paste0(formula, " (", isotopes, ")")
      ) |>
      dplyr::select(-all_of(c("formula", "isotopes"))) |>
      dplyr::rename(formula = full_formula) |>
      dplyr::relocate(formula, .after = name)
  }
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
    write_to_msp(spectra, args$outfile)
  } else if (args$out_format == "tabular") {
    write_to_table(spectra, args$outfile, args$append_isotopes)
  }
}

# Call the main function
main()
