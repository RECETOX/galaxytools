#!/usr/bin/env Rscript
# Script for running RMassBank pipeline:
#   - part1 (all 8 steps at once)
#   - part2 (generation of MassBank records)
#
# Author: Karolina Trachtova (k.trachtova@gmail.com)
# Original authors of RMassBank: Michael Stravs, Emma Schymanski, Steffen Neumann, Erik Mueller, with contributions from Tobias Schulze 
#
# INPUT1 = settings list
# INPUT2 = compounds csv list
# INPUT3 = mode
# INPUT4 = folder with infolists
# INPUT5 = one or more mzML files
#
# RUN:
# Rscript rmassbank_galaxy_part1.r mysettings.ini Compoundlist.csv pH /path/to/files/1_3_Chlorophenyl_piperazin_2818_pos.mzML /path/to/files/1_3_Trifluoromethylphenyl_piperazin_2819_pos.mzML
#############################################################
# Load libraries
rm(list=ls(all=TRUE))

suppressMessages(library("RMassBank", warn.conflicts = T, quietly = T))

#############################################################
# Read arguments
args = commandArgs(trailingOnly=TRUE)

stt <- args[1] #file with settings
cmp <- args[2] #csv file with compounds
md <- args[3] #mode
inf <- args[4] #folder with csv infolist
files <- (args[5:length(args)]) #one or multiple mzML files

print(paste0("Used settings file: ", stt))
print(paste0("Used compound list: ", cmp))
print(paste0("RMassBank pipeline will be run in mode: ", md))
print(paste0("Input files: ", files))

#############################################################
## PART I
#
# Preparing environment for running RMassBank
print("Preparing environment for part I ...")

## Load file with settings
loadRmbSettings(stt)

## create a workspace
w <- newMsmsWorkspace()

## Load compound list
loadList(cmp)

## Load input files
w@files <- files

# Running RMassBank pipeline part I
print("Running RMassBank pipeline part 1 - all 8 steps...")

prf <- c("results")
w <- msmsWorkflow(w, mode=md, steps=c(1:8), archivename=prf)

## Part II
#
# Preparing environment for running RMassBank
print("Preparing environment for part II ...")

mb <- newMbWorkspace(w)

loadList(cmp)

loadRmbSettings(stt)

print("Loading infolist...")

mb <- resetInfolists(mb)

mb <- loadInfolists(mb, inf)

print("Running RMassBank pipeline for generation of MassBank records...")

mb <- mbWorkflow(mb)
