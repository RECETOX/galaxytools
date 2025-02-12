# customized pairs function
pairs2 <- 
  function (x, labels, panel = points, ..., lower.panel = panel, 
            upper.panel = panel, diag.panel = NULL, text.panel = textPanel, 
            label.pos = 0.5 + has.diag/3, cex.labels = NULL, font.labels = 1, 
            row1attop = TRUE, gap = 1) {
    textPanel <- function(x = 0.5, y = 0.5, txt, cex, font) text(x, 
                                                                 y, txt, cex = cex, font = font)
    localAxis <- function(side, x, y, xpd, bg, col = NULL, main, 
                          oma, ...) {
      Axis(y, side = side, xpd = NA, ...)
      Axis(x, side = side, xpd = NA, ...)
    }
    localPlot <- function(..., main, oma, font.main, cex.main) plot(...)
    localLowerPanel <- function(..., main, oma, font.main, cex.main) lower.panel(...)
    localUpperPanel <- function(..., main, oma, font.main, cex.main) upper.panel(...)
    localDiagPanel <- function(..., main, oma, font.main, cex.main) diag.panel(...)
    dots <- list(...)
    nmdots <- names(dots)
    if (!is.matrix(x)) {
      x <- as.data.frame(x)
      for (i in seq_along(names(x))) {
        if (is.factor(x[[i]]) || is.logical(x[[i]])) 
          x[[i]] <- as.numeric(x[[i]])
        if (!is.numeric(unclass(x[[i]]))) 
          stop("non-numeric argument to 'pairs'")
      }
    }
    else if (!is.numeric(x)) 
      stop("non-numeric argument to 'pairs'")
    panel <- match.fun(panel)
    if ((has.lower <- !is.null(lower.panel)) && !missing(lower.panel)) 
      lower.panel <- match.fun(lower.panel)
    if ((has.upper <- !is.null(upper.panel)) && !missing(upper.panel)) 
      upper.panel <- match.fun(upper.panel)
    if ((has.diag <- !is.null(diag.panel)) && !missing(diag.panel)) 
      diag.panel <- match.fun(diag.panel)
    if (row1attop) {
      tmp <- lower.panel
      lower.panel <- upper.panel
      upper.panel <- tmp
      tmp <- has.lower
      has.lower <- has.upper
      has.upper <- tmp
    }
    nc <- ncol(x)
    if (nc < 2) 
      stop("only one column in the argument to 'pairs'")
    has.labs <- TRUE
    if (missing(labels)) {
      labels <- colnames(x)
      if (is.null(labels)) 
        labels <- paste("var", 1L:nc)
    }
    else if (is.null(labels)) 
      has.labs <- FALSE
    oma <- if ("oma" %in% nmdots) 
      dots$oma
    else NULL
    main <- if ("main" %in% nmdots) 
      dots$main
    else NULL
    if (is.null(oma)) {
      oma <- c(4, 4, 4, 4)
      if (!is.null(main)) 
        oma[3L] <- 6
    }
    opar <- par(mfrow = c(nc, nc), mar = rep.int(gap/2, 4), oma = oma)
    on.exit(par(opar))
    dev.hold()
    on.exit(dev.flush(), add = TRUE)
    for (i in if (row1attop) 
      1L:nc
      else nc:1L) for (j in 1L:nc) {
        localPlot(x[, j], x[, i], xlab = "", ylab = "", axes = FALSE, 
                  type = "n", ...)
        if (i == j || (i < j && has.lower) || (i > j && has.upper)) {
          box()
          if (i == nc) {
            localAxis(1, x[, j], x[, i], 
                      ...)
            text(x = mean(xlim), y = ylim[1]-((ylim[2]-ylim[1])*0.35), 
                 labels = labels[j], xpd = NA, cex = cex.labels, font=2)
            }
          if (j == 1) {
            localAxis(2, x[, j], x[, i], ...)
            text(x = xlim[1]-((xlim[2]-xlim[1])*0.35), y = mean(ylim), 
                 labels = labels[i], xpd = NA, srt = 90, cex = cex.labels, font=2)
                        }
            #mtext(text = labels[i], side=2, line=0.5, cex = cex.labels/1.5, font = 2)
            #mtext(text = labels[j], side=3, line=0.5, cex = cex.labels/1.5, font = 2)
          mfg <- par("mfg")
          if (i == j) {
            if (has.diag) 
              localDiagPanel(as.vector(x[, i]), ...)
            if (has.labs) {
              par(usr = c(0, 1, 0, 1))
              if (is.null(cex.labels)) {
                l.wid <- strwidth(labels, "user")
                cex.labels <- max(0.8, min(2, 0.9/max(l.wid)))
              }
              text.panel(0.5, label.pos, labels[i], cex = cex.labels, 
                         font = font.labels)
            }
          }
          else if (i < j) 
            localLowerPanel(as.vector(x[, j]), as.vector(x[, 
                                                           i]), ...)
          else localUpperPanel(as.vector(x[, j]), as.vector(x[, 
                                                              i]), ...)
          if (any(par("mfg") != mfg)) 
            stop("the 'panel' function made a new plot")
        }
        else par(new = FALSE)
      }
    if (!is.null(main)) {
      font.main <- if ("font.main" %in% nmdots) 
        dots$font.main
      else par("font.main")
      cex.main <- if ("cex.main" %in% nmdots) 
        dots$cex.main
      else par("cex.main")
      mtext(main, 3, 3, TRUE, 0.5, cex = cex.main, font = font.main)
    }
    invisible(NULL)
}
  
# load data
data <- knime.in

# load value for data imputation and turn it into a numeric value
if (knime.flow.in[["imputation_value"]] != "None"){
	imp <- as.numeric(knime.flow.in[["imputation_value"]])
}

# set axes limits
if (knime.flow.in[["manual_x_axis_limits"]] != "None"){
 	xlim <- c(as.numeric(knime.flow.in[["manual_x_min"]]),
  			as.numeric(knime.flow.in[["manual_x_max"]]))
} else {
  	xlim <- c(min(data, na.rm = TRUE), max(data, na.rm = TRUE))
}
  
if (knime.flow.in[["manual_y_axis_limits"]] != "None"){
  	ylim <- c(as.numeric(knime.flow.in[["manual_y_min"]]),
  			as.numeric(knime.flow.in[["manual_y_max"]]))
} else if (knime.flow.in[["MAplot"]] == 1){
	variance <- apply(data, 1, function(x) max(x, na.rm = TRUE) - min(x, na.rm = TRUE))
	variance_row <- unlist(data[which.max(variance), ], use.names = FALSE)
	ymin <- min(variance_row, na.rm = TRUE) - max(variance_row, na.rm = TRUE)
	ymax <- max(variance_row, na.rm = TRUE) - min(variance_row, na.rm = TRUE)
	ylim <- c(ymin, ymax)
} else {
  	ylim <- c(min(data, na.rm = TRUE), max(data, na.rm = TRUE))
}

# variables for title offset
l <- 2
oma_down <- 5
oma_up <- 5

# set title for the plot
if (knime.flow.in[["MAplot"]] == 0){
	complete_title = "Density (dark blue->dark red) scatter plot ('y' on 'x') matrix"
} else {
	complete_title = "Density (dark blue->dark red) MA plot ('x-y' on '(x+y)/2') matrix"
}
if (knime.flow.in[["imputation_value"]] != "None"){
	complete_title = paste(complete_title, "\n pairwise imputation by ", 
				 	  as.character(knime.flow.in[["imputation_value"]]), 
				 	  " was done when a single value was missing",
				 	  sep = "")
	l <- l - 0.4
	oma_down <- oma_down - 0.33
	oma_up <- oma_up + 0.33
}
if (knime.flow.in[["regression_type"]] != "none"){
	if (knime.flow.in[["regression_type"]] == "lowess"){
		complete_title = paste(complete_title, "\n red curve is estimated nonparametric lowess model")
	} else {
		complete_title = paste(complete_title, "\n red curve is estimated linear regression model")
	}
	l <- l - 0.4
	oma_down <- oma_down - 0.33
	oma_up <- oma_up + 0.33
}
if (knime.flow.in[["show_unity"]] == 1){
	complete_title = paste(complete_title, "\n dashed line is unity line (x=y)")
	l <- l - 0.4
	oma_down <- oma_down - 0.33
	oma_up <- oma_up + 0.33
}
complete_title = paste(complete_title, "\n ", knime.flow.in[["graph_subtitle"]])

# scatterplot function
panel_scatterplot <- function(x,y, ...) {
  x <- unlist(x)
  y <- unlist(y)
  df <- data.frame(x,y)
  
  if (knime.flow.in[["imputation_value"]] != "None"){
  	df  <- subset(df, df[,1] != imp | df[,2] != imp)
  } else {
  	df <- na.omit(df)	
  }

  x <- unlist(df[,1])
  y <- unlist(df[,2])
  
  x <- densCols(x,y, colramp=colorRampPalette(c("black", "white")))
  df$dens <- col2rgb(x)[1,] + 1L
  cols <-  colorRampPalette(c("#000080", "#004cff", "#29ffce","#ceff29", "#ff6800", "#800000"))(256)
  df$col <- cols[df$dens]
  par(new = TRUE)
  plot(y~x, data = df[order(df$dens),], 
       ylim = ylim, xlim = xlim, pch = 3, col = col,
       cex = 0.5, xlab = "", ylab = "",
       main = "", xaxt = 'n', yaxt = 'n')
       
  if (knime.flow.in[["show_unity"]] == 1){
  	abline(a = 0, b = 1, lty = 2)
  }
  
  if (knime.flow.in[["regression_type"]] == "lowess"){
  	lines(lowess(x = df$x, y = df$y), col = "red")
  } else if(knime.flow.in[["regression_type"]] == "linear"){
  	abline(lm(df$y ~ df$x), col = "red")	
  }
}

# MA function
panel_MA <- function(x,y, ...) {
  x_old <- unlist(x)
  y_old <- unlist(y)
  temp <- data.frame(x_old, y_old)
  
  if (knime.flow.in[["imputation_value"]] != "None"){
  	temp  <- subset(temp, temp[,1] != imp | temp[,2] != imp)
  } else {
  	temp <- na.omit(temp)		
  }
  
  x_old <- unlist(temp[,1])
  y_old <- unlist(temp[,2])
  
  df <- data.frame(x = (x_old + y_old)/2,
  			    y = (x_old - y_old))
  df <- na.omit(df)
  x <- densCols(x_old,y_old, colramp=colorRampPalette(c("black", "white")))
  df$dens <- col2rgb(x)[1,] + 1L
  cols <-  colorRampPalette(c("#000080", "#004cff", "#29ffce","#ceff29", "#ff6800", "#800000"))(256)
  df$col <- cols[df$dens]
  par(new = TRUE)
  plot(y~x, data = df[order(df$dens),], 
       ylim = ylim, xlim = xlim, pch = 3, col = col,
       cex = 0.5, xlab = "", ylab = "",
       main = "", xaxt = 'n', yaxt = 'n')
       
  if (knime.flow.in[["show_unity"]] == 1){
  	abline(h = 0, lty = 2)
  }
  
  if (knime.flow.in[["regression_type"]] == "lowess"){
  	lines(lowess(x = df$x, y = df$y, f = 1/3, iter = 5, delta = 0), col = "red")
  } else if (knime.flow.in[["regression_type"]] == "linear") {
  	abline(lm(df$y ~ df$x), col = "red")	
  }
}

# density function
panel_density <- function(x, ...){
  if (knime.flow.in[["imputation_value"]] != "None"){
  	x <- x[which(x != knime.flow.in[["imputation_value"]])]
  } else {
  	x <- na.omit(x)	
  }
  
  par(new = TRUE)
  dens <- density(x, na.rm = TRUE)
  ylimit <- max(dens$y)*1.5
  plot(dens, main = "", xlab = "", ylab = "", xlim = xlim,
  	ylim = c(0, ylimit), xaxt = 'n', yaxt = 'n')
}

# final plot
par(oma = c(0,0,0,2))
if (knime.flow.in[["MAplot"]] == 1){
	pairs2(data,
      	lower.panel = panel_MA,
      	upper.panel = panel_MA,
      	diag.panel = panel_density,
      	cex.labels = 1,
      	font.labels = 2,
      	cex.axis = 0.75,
      	xlim = xlim,
      	ylim = ylim,
      	gap = 0.5,
      	oma = c(oma_down, 6, oma_up, 4))
} else {
	pairs2(data,
      	lower.panel = panel_scatterplot,
      	upper.panel = panel_scatterplot,
      	diag.panel = panel_density,
      	cex.labels = 1,
      	font.labels = 2,
      	cex.axis = 0.75,
      	xlim = xlim,
      	ylim = ylim,
      	gap = 0.5,
      	oma = c(oma_down, 6, oma_up, 4))
}

title(complete_title, line = l, adj = 0.5, cex.main = 0.65, font.main = 1, xpd=NA)