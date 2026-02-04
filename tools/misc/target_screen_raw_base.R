library(mzR)
markers_file <- "test-data/target_screen/markers.tsv"
mzml_file <- "test-data/raw/centroided.mzml"
rt_range <- 12

ppm <- function(a, b) abs((a - b) / b) * 1e6
err <- function(p, rt, int) sum((int - p[1] * exp(-0.5 * ((rt - p[2]) / p[3])^2))^2)

m <- read.delim(markers_file, stringsAsFactors = FALSE)
m$suspect_idx <- seq_len(nrow(m))
ms <- openMSfile(mzml_file)
h <- header(ms)

scans <- data.frame(suspect_idx = integer(), suspect_mz = double(), suspect_rt = double(),
                    scan_idx = integer(), scan_rt = double(), matched_mz = double(),
                    matched_intensity = double(), ppm_error = double(),
                    stringsAsFactors = FALSE)
for (i in seq_len(nrow(m))) {
  mz <- as.numeric(m$mz[i]); rt0 <- as.numeric(m$rt[i])
  idx <- which(h$retentionTime >= rt0 - rt_range & h$retentionTime <= rt0 + rt_range)
  if (!length(idx)) next
  for (si in idx) {
    pk <- peaks(ms, si)
    if (is.null(pk) || nrow(pk) == 0) next
    j <- which.min(abs(pk[, 1] - mz))
    scans <- rbind(scans, data.frame(suspect_idx = i, suspect_mz = mz, suspect_rt = rt0,
                                     scan_idx = si, scan_rt = h$retentionTime[si],
                                     matched_mz = pk[j, 1], matched_intensity = pk[j, 2],
                                     ppm_error = ppm(pk[j, 1], mz)))
  }
}

if (!nrow(scans)) { close(ms); stop("No matching scans.") }
write.table(scans, "scans.tsv", sep = "\t", row.names = FALSE, quote = FALSE)

fits_df <- data.frame(suspect_idx = integer(), suspect_mz = double(), suspect_rt = double(),
                      fitted_amplitude = double(), fitted_mean = double(), fitted_sd = double(),
                      num_scans = integer(), fit_rmse_norm = double(),
                      stringsAsFactors = FALSE)

for (sid in unique(scans$suspect_idx)) {
  df <- scans[scans$suspect_idx == sid, ]
  rt <- df$scan_rt; int <- df$matched_intensity
  init <- c(max(int), rt[which.max(int)], max(diff(range(rt)) / 4, 1e-3))
  ft <- optim(init, err, rt = rt, int = int, method = "Nelder-Mead")
  if (ft$convergence != 0 || ft$par[3] <= 0) next
  pred <- ft$par[1] * exp(-0.5 * ((rt - ft$par[2]) / ft$par[3])^2)
  rmse <- sqrt(mean((int - pred)^2)) / max(int)
  if (rmse > 0.25) next
  fits_df <- rbind(fits_df, data.frame(suspect_idx = sid, suspect_mz = df$suspect_mz[1], suspect_rt = df$suspect_rt[1],
                                       fitted_amplitude = ft$par[1], fitted_mean = ft$par[2], fitted_sd = ft$par[3],
                                       num_scans = nrow(df), fit_rmse_norm = rmse))
}


write.table(fits_df, "fits.tsv", sep = "\t", row.names = FALSE, quote = FALSE)

pdf("plots.pdf", width = 10, height = 7)
for (k in seq_len(nrow(fits_df))) {
  sid <- fits_df$suspect_idx[k]
  df <- scans[scans$suspect_idx == sid, ]
  rt_win <- c(df$suspect_rt[1] - rt_range, df$suspect_rt[1] + rt_range)
  rt_seq <- seq(rt_win[1], rt_win[2], length.out = 200)
  curve <- fits_df$fitted_amplitude[k] * exp(-0.5 * ((rt_seq - fits_df$fitted_mean[k]) / fits_df$fitted_sd[k])^2)
  plot(df$scan_rt, df$matched_intensity, pch = 16, col = "blue",
       main = paste0("Suspect ", sid, " mz=", round(df$suspect_mz[1], 3)),
       xlab = "Retention Time (s)", ylab = "Intensity", xlim = rt_win)
  lines(rt_seq, curve, col = "red", lwd = 2)
}
dev.off()


close(ms)
