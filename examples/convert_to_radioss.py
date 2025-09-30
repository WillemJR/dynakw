
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
        for kw in dkw.keywords():
            if kw.type == dynakw.KeywordType.NODE:
                f.write("/NODE\n")
                card = kw.cards['Card 1']
                for i in range(len(card['NID'])):
                    f.write(
                        f"{card['NID'][i]} {card['X'][i]} {card['Y'][i]} {card['Z'][i]}\n")
            elif kw.type == dynakw.KeywordType.ELEMENT_SHELL:
                f.write("/SHELL\n")
                card = kw.cards['Card 1']
                for i in range(len(card['EID'])):
                    f.write(
                        f"{card['EID'][i]} {card['PID'][i]} {card['N1'][i]} {card['N2'][i]} {card['N3'][i]} {card['N4'][i]}\n")
            elif kw.type == dynakw.KeywordType.ELEMENT_SOLID:
                f.write("/SOLID\n")
                card = kw.cards['Card 1']
                for i in range(len(card['EID'])):
                    f.write(
                        f"{card['EID'][i]} {card['PID'][i]} {card['N1'][i]} {card['N2'][i]} {card['N3'][i]} {card['N4'][i]} {card['N5'][i]} {card['N6'][i]} {card['N7'][i]} {card['N8'][i]}\n")
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
        f.write(f"/END\n")


# Set up argument parser
parser = argparse.ArgumentParser(
    description="Translate LS-DYNA keyword file to a Radioss one.")
parser.add_argument(
    "input_file", help="Path to the input LS-DYNA keyword file.")
args = parser.parse_args()

# Read the file
fname = args.input_file
dkw = dynakw.DynaKeywordReader(fname)

# Determine output filename
base_fname, _ = os.path.splitext(fname)
out_fname = base_fname + ".rad"

write_as_radioss(dkw, out_fname)
