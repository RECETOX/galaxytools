import sys

# Script that creates a .ini settings file for RMassBank pipeline
# Intended to be wrapped as a tool to Galaxy (in docker) to create users of RMassBank the mysettings.ini file -> very "stupid" script, does not check correctness of user's input, that will do Galaxy XML wrapper
# INPUT: mysettings.ini (default file downloaded via R package RMassBank, will be stored in the docker)
#
# python script.py mysettings.ini 0.34 0.34 34 FALSE FALSE 34 34 34 34 34 0.34 dmz none 34 34 34 34 34 34 34 34 34 34 34 0.34 0.34 0.34 34 0.34 TRUE /babeldir/path FALSE charged

fin = open(sys.argv[1], "r")
fout = open("mysettings_galaxy.ini", "wt")

for line in fin:
	if "rtMargin:" in line:
		fout.write("rtMargin: "+sys.argv[2]+"\n")
	elif "rtShift:" in line:
		fout.write("rtShift: "+sys.argv[3]+"\n")
	elif "babeldir:" in line and "#" not in line:
		fout.write("babeldir: '"+sys.argv[32]+"'\n") 
	elif "use_version:" in line:
		fout.write("use_version: "+sys.argv[4]+"\n")
	elif "use_rean_peaks:" in line:
		fout.write("use_rean_peaks: "+sys.argv[5]+"\n")
	elif "add_annotation:" in line:
		fout.write("add_annotation: "+sys.argv[6]+"\n")
	elif "include_sp_tags:" in line:
		fout.write("include_sp_tags: "+sys.argv[33]+"\n")
	elif "pH:" in line:
		fout.write("    pH: "+sys.argv[7]+" # [M+H]+: Accession numbers 1-14\n")
	elif "pM:" in line:
		fout.write("    pM: "+sys.argv[8]+" # [M]+: 17-30\n")
	elif "pNa:" in line:
		fout.write("    pNa: "+sys.argv[9]+" # [M+Na]+: 33-46\n")
	elif "mH:" in line:
		fout.write("    mH: "+sys.argv[10]+" # [M-H]-: 51-64\n")
	elif "mFA:" in line:
		fout.write("    mFA: "+sys.argv[11]+" # [M+FA]-: 67-80\n")
	elif "electronicNoiseWidth:" in line:
		fout.write("electronicNoiseWidth: "+sys.argv[12]+"\n")
	elif "recalibrateBy:" in line:
		fout.write("recalibrateBy: "+sys.argv[13]+"\n")
	elif "recalibrateMS1:" in line:
		fout.write("recalibrateMS1: "+sys.argv[14]+"\n")
	elif "recalibrateMS1Window:" in line:
		fout.write("recalibrateMS1Window: "+sys.argv[15]+"\n")
	elif "multiplicityFilter:" in line:
		fout.write("multiplicityFilter: "+sys.argv[16]+"\n")
	elif "ppmHighMass:" in line:
		fout.write("    ppmHighMass: "+sys.argv[17]+"\n")
	elif "ppmLowMass:" in line:
		fout.write("    ppmLowMass: "+sys.argv[18]+"\n")
	elif "massRangeDivision:" in line:
		fout.write("    massRangeDivision: "+sys.argv[19]+"\n")
	elif "ppmFine:" in line:
		fout.write("    ppmFine: "+sys.argv[20]+"\n")
	elif "prelimCut:" in line:
		fout.write("    prelimCut: "+sys.argv[21]+"\n")
	elif "prelimCutRatio:" in line:
		fout.write("    prelimCutRatio: "+sys.argv[22]+"\n")
	elif "fineCut:" in line:
		fout.write("    fineCut: "+sys.argv[23]+"\n")
	elif "fineCutRatio:" in line:
		fout.write("    fineCutRatio: "+sys.argv[24]+"\n")
	elif "specOkLimit:" in line:
		fout.write("    specOkLimit: "+sys.argv[25]+"\n")
	elif "dbeMinLimit:" in line:
		fout.write("    dbeMinLimit: "+sys.argv[26]+"\n")
	elif "satelliteMzLimit:" in line:
		fout.write("    satelliteMzLimit: "+sys.argv[27]+"\n")
	elif "satelliteIntLimit:" in line:
		fout.write("    satelliteIntLimit: "+sys.argv[28]+"\n")
	elif "ppmFine:" in line:
		fout.write("    ppmFine: "+sys.argv[29]+"\n")
	elif "mzCoarse:" in line:
		fout.write("    mzCoarse: "+sys.argv[30]+"\n")
	elif "fillPrecursorScan:" in line:
		fout.write("    fillPrecursorScan: "+sys.argv[31]+"\n")
	elif "unknownMass:" in line:
		fout.write("unknownMass: "+sys.argv[34]+"\n")
	else:
		fout.write(line)
fin.close()
fout.close()
