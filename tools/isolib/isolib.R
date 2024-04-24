library(enviPat)
library(Spectra)
library(MsBackendMsp)
library(MetaboCoreUtils)
library(readr)

#' @param args A list of command line arguments.
main <- function() {
  data(isotopes)
  data(adducts)

  args <- commandArgs(trailingOnly = TRUE)
  compound_table <- read_tsv(
    file = args[1],
    col_types = "ccd",
    col_select = c("name", "formula", "rt")
  )
  adducts_to_use <- c(unlist(strsplit(args[2], ",", fixed = TRUE)))

  chemforms <- compound_table$formula
  chemforms <- check_chemform(isotopes, chemforms)[, 2]

  spectra <- data.frame()

  for (current in adducts_to_use) {
    adduct <- adducts[adducts$Name == current, ]
    multiplied_chemforms <- multiform(chemforms, adduct$Mult)

    if (adduct$Ion_mode == "negative") {
      merged_chemforms <- subform(multiplied_chemforms, adduct$Formula_ded)
    } else {
      merged_chemforms <- mergeform(multiplied_chemforms, adduct$Formula_add)
    }

    charge_string <- paste0(if (adduct$Charge > 0) "+" else "-", if (abs(adduct$Charge) > 1) abs(adduct$Charge) else "")
    adduct_string <- paste0("[", adduct$Name, "]", charge_string)
    precursor_mz <- calculateMass(multiplied_chemforms) + adduct$Mass

    if (args[4] == TRUE) {
      names <- paste(compound_table$name, paste0("(", adduct$Name, ")"), sep = " ")
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
      threshold = as.numeric(args[3]),
    )

    mzs <- list()
    intensities <- list()
    for (i in seq_along(patterns)) {
      mzs <- append(mzs, list(patterns[[i]][, 1]))
      intensities <- append(intensities, list(patterns[[i]][, 2]))
    }

    spectra_df$mz <- mzs
    spectra_df$intensity <- intensities
    spectra <- rbind(spectra, spectra_df)
  }

  sps <- Spectra(spectra)
  export(sps, MsBackendMsp(), file = args[5])
}

# Get the command line arguments
args <- commandArgs(trailingOnly = TRUE)
# Call the main function
main()
