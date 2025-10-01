
import os
import argparse
import sys
sys.path.append('.')
import dynakw


def write_as_radioss(dkw: dynakw.DynaKeywordReader, out_fname: str):
    """ Translate LS-DYNA keyword file to a Radioss one.

    Args:
      dkw (dynakw.DynaKeywordReader) :
      out_fname (str) :
    """

    with open(out_fname, "w") as f:
        f.write(
"""#---1----|----2----|----3----|----4----|----5----|----6----|----7----|----8----|----9----|---10----|
/BEGIN
fix below !!!
      2025         0
                  Mg                  mm                   s
                  Mg                  mm                   s
#---1----|----2----|----3----|----4----|----5----|----6----|----7----|----8----|----9----|---10----|
"""
                )
        for kw in dkw.keywords():
            if kw.type == dynakw.KeywordType.NODE:
                f.write("/NODE\n")
                card = kw.cards['Card 1']
                for i in range(len(card['NID'])):
                    f.write(
                            f"{card['NID'][i]:10d}{card['X'][i]:10.3g}{card['Y'][i]:10.3g}{card['Z'][i]:10.3g}\n")
            elif kw.type == dynakw.KeywordType.ELEMENT_SHELL:
                card = kw.cards['Card 1']
                for pid in set(card['PID']):
                  f.write(f"/SHELL/{pid}\n")
                  for i in range(len(card['EID'])):
                    if pid == card['PID'][i]:
                      f.write(
                            f"{card['EID'][i]:10d}{card['N1'][i]:10d}{card['N2'][i]:10d}{card['N3'][i]:10d}{card['N4'][i]:10d}\n")
            elif kw.type == dynakw.KeywordType.ELEMENT_SOLID:
                # NYI: must be sorted according to /BRIC20, BRICK, PENTA6, QUAD, SHEL16, TETRA10, TETRA4, TRIA
                card = kw.cards['Card 1']
                for pid in set(card['PID']):
                  f.write(f"/BRICK/{pid}\n")
                  for i in range(len(card['EID'])):
                    if pid == card['PID'][i]:
                      f.write(
                            f"{card['EID'][i]:10d}{card['N1'][i]:10d}{card['N2'][i]:10d}{card['N3'][i]:10d}{card['N4'][i]:10d}{card['N5'][i]:10d}{card['N6'][i]:10d}{card['N7'][i]:10d}{card['N8'][i]:10d}\n")

            # Below must still be debugged.
            """
            elif kw.type == dynakw.KeywordType.PART:
                f.write("/PART\n")
                card1 = kw.cards['Card 1']
                card2 = kw.cards['Card 2']
                for i in range(len(card1['PID'])):
                    f.write(f"{card1['HEADING'][i]}\n")
                    f.write(
                        f"{card2['PID'][i]} {card2['SECID'][i]} {card2['MID'][i]}\n")
            elif kw.type == dynakw.KeywordType.MAT_ELASTIC:
                f.write("/MAT/ELASTIC\n")
                card = kw.cards['card1']
                for i in range(len(card['MID'])):
                    f.write(
                        f"{card['MID'][i]} {card['RO'][i]} {card['E'][i]} {card['PR'][i]}\n")
            elif kw.type == dynakw.KeywordType.SECTION_SHELL:
                f.write("/SECTION/SHELL\n")
                card1 = kw.cards['Card 1']
                card2 = kw.cards['Card 2']
                for i in range(len(card1['SECID'])):
                    f.write(f"{card1['SECID'][i]} {card1['ELFORM'][i]}\n")
                    f.write(
                        f"{card2['T1'][i]} {card2['T2'][i]} {card2['T3'][i]} {card2['T4'][i]}\n")
            elif kw.type == dynakw.KeywordType.SECTION_SOLID:
                f.write("/SECTION/SOLID\n")
                card = kw.cards['Card 1']
                for i in range(len(card['SECID'])):
                    f.write(f"{card['SECID'][i]} {card['ELFORM'][i]}\n")
            """
        f.write(f"/END\n")


# Set up argument parser
parser = argparse.ArgumentParser(
    description="Translate LS-DYNA keyword file to a Radioss one.")
parser.add_argument(
    "input_file", help="Path to the input LS-DYNA keyword file.")
args = parser.parse_args()

# Read the file
fname = args.input_file
dkw = dynakw.DynaKeywordReader(fname, debug=False)

# Determine output filename
base_fname, _ = os.path.splitext(fname)
out_fname = base_fname + ".rad"

write_as_radioss(dkw, out_fname)
