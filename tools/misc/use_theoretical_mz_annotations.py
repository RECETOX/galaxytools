from typing import Tuple, Iterator
import argparse

def get_peak_values(peak: str) -> Tuple[float, float, str]:
    """ Get the m/z and intensity value from the line containing the peak information. """
    splitted_line = peak.split(maxsplit=2)
    mz = float(splitted_line[0].strip())
    intensity = float(splitted_line[1].strip())
    comment = ''
    if(len(splitted_line) == 3):
        comment = splitted_line[2].strip()
    return mz, intensity, comment

def get_peak_tuples(rline: str) -> Iterator[str]:
    """ Splits line at ';' and performs additional string cleaning. """
    tokens = filter(None, rline.split(";"))
    peak_pairs = map(lambda x: x.lstrip().rstrip(), tokens)
    return peak_pairs

def overwrite_peaks(file: str, output: str, only_contains_annotation: bool = False) -> None:
    """This function overwrites peaks in the input file with annotated peaks.

    Args:
        file (str): The path to the input file.
        output (str): The path to the output file.
        only_contains_annotation (bool, optional): If True, only peaks with annotations are processed. Defaults to False.

    Returns:
        None: The function writes the output to a file and does not return anything.
    """
    annotated_msp = []
    annotated_msp_list = []
    
    with open(file,'r') as file:
        while True:
            line = file.readline()
            if not line.strip():
                if len(peaks) > 0:
                    annotated_msp_list.append(annotated_msp)
                annotated_msp = []
            if line == '':
                break
            if line.startswith('Num Peaks:'):
                num_peaks = int(line.split(':')[1].strip())
                peaks = []
                for i in range(num_peaks):
                    line = file.readline()
                    peak_pairs = get_peak_tuples(line)
                    
                    for peak in peak_pairs:
                        mz, intensity, comment = get_peak_values(peak)
                        if comment != '':
                            tokens = comment.split()
                            mz = float(tokens[2].strip().rstrip(','))
                            peak_text = '%s\t%s\t%s\n' % (str(mz), str(intensity), str(comment))
                            peaks.append(peak_text)
                        
                        if only_contains_annotation == False and comment == '':
                            peak_text = '%s\t%s\n' % (str(mz), str(intensity))
                            peaks.append(peak_text)
                            
                annotated_msp.append("Num Peaks: %d\n" % len(peaks))
                for item in peaks:
                    annotated_msp.append(item)
            else:
                annotated_msp.append(line)
    
    with open(output,'w') as file:
        for spectra in annotated_msp_list:
            file.writelines(spectra)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_filename', type=str, required=True, help='Input file name')
    parser.add_argument('-o', '--output_filename', type=str, required=True, help='Output file name')
    parser.add_argument('-a', '--annotated', action='store_true', help='Process only peaks with annotations')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    overwrite_peaks(args.input_filename, args.output_filename, args.annotated)
