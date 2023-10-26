library(enviPat)
library(dplyr)
library(Spectra)
library(MsBackendMsp)
library(MetaboCoreUtils)

data(isotopes)
data(adducts)

adducts_to_use <- c("M-H", "2M-H")

compound_table <- read.csv("lc_markers_neg.csv", stringsAsFactors = FALSE)
chemforms <- compound_table$formula
chemforms <- check_chemform(isotopes, chemforms)[,2]


spectra <- data.frame()

for (current in adducts_to_use) {
    adduct <- adducts[adducts$Name == current,]
    multiplied_chemforms <- multiform(chemforms, adduct$Mult)

    if(adduct$Ion_mode == "negative") {
        merged_chemforms <- subform(multiplied_chemforms, adduct$Formula_ded)
    } else {
        merged_chemforms <- mergeform(multiplied_chemforms, adduct$Formula_add)
    }

    charge_string <- paste0(if(adduct$Charge > 0) "+" else "-", if(abs(adduct$Charge) > 1) abs(adduct$Charge) else "")
    adduct_string <- paste0("[", adduct$Name, "]", charge_string)
    precursor_mz <- calculateMass(multiplied_chemforms) + adduct$Mass
    
    spectra_df <- data.frame(
        name=compound_table$name,
        adduct=adduct_string,
        formula=chemforms,
        retention_time=compound_table$rt,
        charge=adduct$Charge,
        ionization_mode=adduct$Ion_mode,
        precursor_mz=precursor_mz
    )

    patterns <- enviPat::isopattern(
        isotopes=isotopes,
        chemforms=merged_chemforms,
        charge=1,
    )

    mzs <- list()
    intensities <- list()
    for (i in 1:length(patterns)) {
        mzs <- append(mzs, list(patterns[[i]][,1]))
        intensities <- append(intensities, list(patterns[[i]][,2]))
    }

    spectra_df$mz <- mzs
    spectra_df$intensity <- intensities
    spectra <- rbind(spectra, spectra_df)
}

sps <- Spectra(spectra)
export(sps, MsBackendMsp(), file="lc_markers_neg_R.msp")

