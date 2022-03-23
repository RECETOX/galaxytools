import subprocess
import sys
import tempfile
import re
import pandas

from openbabel import openbabel, pybel
openbabel.obErrorLog.StopLogging()


def InchiToSmiles(df):
    '''Translate inchi to smiles'''
    sm = []
    for item in df['InChI']:
        tmp = pybel.readstring("inchi", item)
        sm.append(tmp.write("smi"))
    return(sm)


executable = ["biotransformer"]

argv = sys.argv[1:]
icsv = argv.pop(argv.index("-icsv") + 1)
argv.remove("-icsv")
ocsv = argv.pop(argv.index("-ocsv") + 1)
argv.remove("-ocsv")
ocsv_dup = argv.pop(argv.index("-ocsvDup") + 1)
argv.remove("-ocsvDup")
ocsv_dup2 = argv.pop(argv.index("-ocsvDup2") + 1)
argv.remove("-ocsvDup2")

in_df = pandas.read_csv(icsv, header=None)
out_df1 = pandas.DataFrame()  # all results
out_df2 = pandas.DataFrame()  # filtered results based on 6 columns
out_df3 = pandas.DataFrame()  # filtered results based on 3 columns

smList1 = []  # list with smiles string
smList2 = []
smList3 = []
for _, (smiles,) in in_df.iterrows():
    with tempfile.NamedTemporaryFile() as out:
        print("Working on compound: " + smiles)
        if not re.search(r'\.', smiles):
            subprocess.run(executable + argv + ["-ismi", smiles] + ["-ocsv", out.name])
            try:
                bio_out = pandas.read_csv(out.name)
                tmp2 = bio_out.drop_duplicates(subset=["InChI", "InChIKey", "Synonyms", "Molecular formula", "Major Isotope Mass", "ALogP"])
                tmp3 = bio_out.drop_duplicates(subset=["Molecular formula", "Major Isotope Mass", "ALogP"])

                smList1.append([smiles] * bio_out.shape[0])
                smList2.append([smiles] * tmp2.shape[0])
                smList3.append([smiles] * tmp3.shape[0])

                out_df1 = pandas.concat([out_df1, bio_out])
                out_df2 = pandas.concat([out_df2, tmp2])
                out_df3 = pandas.concat([out_df3, tmp3])
            except pandas.errors.EmptyDataError:
                continue
        else:
            print("ERROR: Input compound cannot be a mixture.")
smList1 = sum(smList1, [])  # merge sublists into one list
smList2 = sum(smList2, [])
smList3 = sum(smList3, [])

out_df1.insert(0, "SMILES query", smList1)
out_df1.insert(1, "SMILES target", InchiToSmiles(out_df1))
out_df1.to_csv(ocsv, sep ='\t')

out_df2.insert(0, "SMILES query", smList2)
out_df2.insert(1, "SMILES target", InchiToSmiles(out_df2))
out_df2.to_csv(ocsv_dup, sep ='\t')

out_df3.insert(0, "SMILES query", smList3)
out_df3.insert(1, "SMILES target", InchiToSmiles(out_df3))
out_df3.to_csv(ocsv_dup2, sep ='\t')
