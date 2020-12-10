import subprocess
import sys
import tempfile
import re
import pandas

from openbabel import openbabel, pybel
openbabel.obErrorLog.StopLogging()


# function for translating inchi to smiles
def InchiToSmiles(df):
    sm = []
    for item in df['InChI']:
        tmp = pybel.readstring("inchi", item)
        sm.append(tmp.write("smi"))
    return(sm)


executable = ["biotransformer"]
# executable_r = ["Rscript", "inchi_to_smiles.r"]

argv = sys.argv[1:]
if "-icsv" in argv:
    icsv = argv.pop(argv.index("-icsv") + 1)
    argv.remove("-icsv")

    if "-ocsv" not in argv:
        sys.stderr.write("excpected -ocsv parameter\n")
        sys.exit(1)
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

    tmp2 = pandas.DataFrame()
    tmp3 = pandas.DataFrame()

    smList1 = []  # list with smiles string
    smList2 = []
    smList3 = []
    for _, (smiles,) in in_df.iterrows():
        with tempfile.NamedTemporaryFile() as out:
            print("Working on compound: " + smiles)
            if not re.search(r'\.', smiles):
                subprocess.run(executable + argv + ["-ismi", smiles] + ["-ocsv", out.name])
                try:
                    tmp2 = pandas.read_csv(out.name)
                    tmp3 = pandas.read_csv(out.name)
                    tmp2.drop_duplicates(inplace=True, subset=["InChI", "InChIKey", "Synonyms", "Molecular formula", "Major Isotope Mass", "ALogP"])
                    tmp3.drop_duplicates(inplace=True, subset=["Molecular formula", "Major Isotope Mass", "ALogP"])
                    smList2.append([smiles] * tmp2.shape[0])
                    smList3.append([smiles] * tmp3.shape[0])
                    out_df1 = pandas.concat([out_df1, pandas.read_csv(out.name)])
                    out_df2 = pandas.concat([out_df2, tmp2])
                    out_df3 = pandas.concat([out_df3, tmp3])
                    smList1.append([smiles] * pandas.read_csv(out.name).shape[0])
                except pandas.errors.EmptyDataError:
                    continue
            else:
                print("ERROR: Input compound cannot be a mixture.")
    smList1 = sum(smList1, [])  # merge sublists into one list
    smList2 = sum(smList2, [])
    smList3 = sum(smList3, [])

    out_df1.insert(0, "SMILES query", smList1)
    out_df1.drop_duplicates(inplace=True)
    out_df1.insert(1, "SMILES target", InchiToSmiles(out_df1))
    out_df1.to_csv(ocsv)

    out_df2.insert(0, "SMILES query", smList2)
    out_df3.insert(0, "SMILES query", smList3)
    out_df2.drop_duplicates(inplace=True)
    out_df3.drop_duplicates(inplace=True)
    out_df2.insert(1, "SMILES target", InchiToSmiles(out_df2))
    out_df3.insert(1, "SMILES target", InchiToSmiles(out_df3))
    # out_df.drop_duplicates(inplace=True, subset=["InChI", "InChIKey", "Synonyms", "Molecular formula", "Major Isotope Mass", "ALogP"])
    out_df2.to_csv(ocsv_dup)
    out_df3.to_csv(ocsv_dup2)
else:
    # code = subprocess.run(executable + argv).returncode
    # sys.exit(code)
    subprocess.run(executable + argv)
    smile = argv.pop(argv.index("-ismi") + 1)
    tmp = pandas.DataFrame()
    out = argv.pop(argv.index("-ocsv") + 1)
    tmp = pandas.read_csv(out)   # reads created output file
    tmp.insert(0, "SMILES query", smile)  # add SMILES string for query
    tmp.insert(1, "SMILES target", InchiToSmiles(tmp))  # add SMILES string for target
    tmp.to_csv(out)
