import sys

# Script that replaces OpenBabel path in settings file used within Galaxy (tools installed via conda)#
# python script.py /path/settings_file /babeldir/path

fin = open(sys.argv[1], "r")
fout = open("mysettings_galaxy.ini", "wt")

for line in fin:
	if "babeldir:" in line and "#" not in line:
		fout.write("babeldir: '"+sys.argv[2]+"'\n") 
	else:
		fout.write(line)
fin.close()
fout.close()
