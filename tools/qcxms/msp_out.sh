#!/bin/sh

molname=`sed -n '2{p;q}'  TMPQCXMS/TMP.1/start.xyz`
kword=$(grep 'NPOINTS' result.jdx)
num_peaks=$(echo "$kword" | sed 's/^[^=]*=//')
echo `pwd`
sed -n '/PEAK/,/END/{/PEAK/!{/END/!p}}' result.jdx > temp.dat
awk '{print $1, $2}' temp.dat > tempa.dat
sed "1s/^/NAME: $molname\nNum Peaks: $num_peaks\n/" tempa.dat >> simulated_spectra.msp
sed -i '$a\ ' simulated_spectra.msp
rm temp.dat tempa.dat