"""Implementation of the *PART keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class Part(LSDynaKeyword):
    """
    Implements the *PART keyword.
    """
    keyword_string = "*PART"

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parses the raw data for *PART."""
        active_options = {opt.upper() for opt in self.options}

        headings, main_data, inertia_data, reposition_data, contact_data, print_data, attachment_nodes_data, field_data = [
        ], [], [], [], [], [], [], []

        card_lines = [line.strip() for line in raw_lines[1:]
                      if not line.startswith('$')]

        if not card_lines:
            return

        i = 0
        while i < len(card_lines):
            # Card 1: HEADING
            heading = card_lines[i].strip()
            i += 1
            if i >= len(card_lines):
                break

            # Card 2: Main Definition
            main_fields = self.parser.parse_line(
                card_lines[i], ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'])
            pid = main_fields[0]
            if pid is None:
                continue

            headings.append({'PID': pid, 'HEADING': heading})
            main_data.append({
                'PID': pid, 'SECID': main_fields[1], 'MID': main_fields[2], 'EOSID': main_fields[3],
                'HGID': main_fields[4], 'GRAV': main_fields[5], 'ADPOPT': main_fields[6], 'TMID': main_fields[7]
            })
            i += 1

            # Optional Cards
            if 'INERTIA' in active_options:
                if i + 2 >= len(card_lines):
                    break
                inertia_card3 = self.parser.parse_line(
                    card_lines[i], ['F', 'F', 'F', 'F', 'I', 'I'])
                inertia_card4 = self.parser.parse_line(
                    card_lines[i + 1], ['F', 'F', 'F', 'F', 'F', 'F'])
                inertia_card5 = self.parser.parse_line(
                    card_lines[i + 2], ['F', 'F', 'F', 'F', 'F', 'F'])
                i += 3

                inertia_record = {
                    'PID': pid,
                    'XC': inertia_card3[0], 'YC': inertia_card3[1], 'ZC': inertia_card3[2],
                    'TM': inertia_card3[3], 'IRCS': inertia_card3[4], 'NODEID': inertia_card3[5],
                    'IXX': inertia_card4[0], 'IXY': inertia_card4[1], 'IXZ': inertia_card4[2],
                    'IYY': inertia_card4[3], 'IYZ': inertia_card4[4], 'IZZ': inertia_card4[5],
                    'VTX': inertia_card5[0], 'VTY': inertia_card5[1], 'VTZ': inertia_card5[2],
                    'VRX': inertia_card5[3], 'VRY': inertia_card5[4], 'VRZ': inertia_card5[5]
                }

                if inertia_card3[4] == 1:
                    if i >= len(card_lines):
                        break
                    inertia_card6 = self.parser.parse_line(
                        card_lines[i], ['F', 'F', 'F', 'F', 'F', 'F', 'I'])
                    i += 1
                    inertia_record.update({
                        'XL': inertia_card6[0], 'YL': inertia_card6[1], 'ZL': inertia_card6[2],
                        'XLIP': inertia_card6[3], 'YLIP': inertia_card6[4], 'ZLIP': inertia_card6[5],
                        'CID': inertia_card6[6]
                    })
                inertia_data.append(inertia_record)

            if 'REPOSITION' in active_options:
                if i >= len(card_lines):
                    break
                repo_card = self.parser.parse_line(
                    card_lines[i], ['I', 'I', 'I'])
                i += 1
                reposition_data.append(
                    {'PID': pid, 'CMSN': repo_card[0], 'MDEP': repo_card[1], 'MOVOPT': repo_card[2]})

            if 'CONTACT' in active_options:
                if i >= len(card_lines):
                    break
                contact_card = self.parser.parse_line(
                    card_lines[i], ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F'])
                i += 1
                contact_data.append({'PID': pid, 'FS': contact_card[0], 'FD': contact_card[1], 'DC': contact_card[2], 'VC': contact_card[3],
                                    'OPTT': contact_card[4], 'SFT': contact_card[5], 'SSF': contact_card[6], 'CPARM8': contact_card[7]})

            if 'PRINT' in active_options:
                if i >= len(card_lines):
                    break
                print_card = self.parser.parse_line(card_lines[i], ['F'])
                i += 1
                print_data.append({'PID': pid, 'PRBF': print_card[0]})

            if 'ATTACHMENT_NODES' in active_options:
                if i >= len(card_lines):
                    break
                attach_card = self.parser.parse_line(card_lines[i], ['I'])
                i += 1
                attachment_nodes_data.append(
                    {'PID': pid, 'ANSID': attach_card[0]})

            if 'FIELD' in active_options:
                if i >= len(card_lines):
                    break
                field_card = self.parser.parse_line(card_lines[i], ['I'])
                i += 1
                field_data.append({'PID': pid, 'FIDBO': field_card[0]})

        # Convert lists of dicts to dict of numpy arrays (column-major)
        def records_to_col_dict(records, cols):
            if not records:
                return {col: np.array([], dtype=object) for col in cols}
            arr = np.array([[rec.get(col) for col in cols]
                           for rec in records], dtype=object)
            return {col: arr[:, i] for i, col in enumerate(cols)}

        if headings:
            cols = ['PID', 'HEADING']
            self.cards['Card 1'] = records_to_col_dict(headings, cols)
        if main_data:
            cols = ['PID', 'SECID', 'MID', 'EOSID',
                    'HGID', 'GRAV', 'ADPOPT', 'TMID']
            self.cards['Card 2'] = records_to_col_dict(main_data, cols)
        if inertia_data:
            cols = ['PID', 'XC', 'YC', 'ZC', 'TM', 'IRCS', 'NODEID', 'IXX', 'IXY', 'IXZ', 'IYY', 'IYZ', 'IZZ',
                    'VTX', 'VTY', 'VTZ', 'VRX', 'VRY', 'VRZ', 'XL', 'YL', 'ZL', 'XLIP', 'YLIP', 'ZLIP', 'CID']
            self.cards['inertia'] = records_to_col_dict(inertia_data, cols)
        if reposition_data:
            cols = ['PID', 'CMSN', 'MDEP', 'MOVOPT']
            self.cards['reposition'] = records_to_col_dict(
                reposition_data, cols)
        if contact_data:
            cols = ['PID', 'FS', 'FD', 'DC', 'VC',
                    'OPTT', 'SFT', 'SSF', 'CPARM8']
            self.cards['contact'] = records_to_col_dict(contact_data, cols)
        if print_data:
            cols = ['PID', 'PRBF']
            self.cards['print'] = records_to_col_dict(print_data, cols)
        if attachment_nodes_data:
            cols = ['PID', 'ANSID']
            self.cards['attachment_nodes'] = records_to_col_dict(
                attachment_nodes_data, cols)
        if field_data:
            cols = ['PID', 'FIDBO']
            self.cards['field'] = records_to_col_dict(field_data, cols)

    def write(self, file_obj: TextIO):
        """Writes the *PART keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        main = self.cards.get("Card 2")
        if main is None or len(main['PID']) == 0:
            return

        headings = self.cards.get("Card 1")
        inertia = self.cards.get("inertia")
        reposition = self.cards.get("reposition")
        contact = self.cards.get("contact")
        print_card = self.cards.get("print")
        attachment_nodes = self.cards.get("attachment_nodes")
        field = self.cards.get("field")

        n_parts = len(main['PID'])
        for idx in range(n_parts):
            pid = main['PID'][idx]

            # Heading
            if headings is not None:
                heading_idx = np.where(headings['PID'] == pid)[0]
                if heading_idx.size > 0:
                    file_obj.write(f"{headings['HEADING'][heading_idx[0]]}\n")

            # Main card
            main_cols = ['PID', 'SECID', 'MID', 'EOSID',
                         'HGID', 'GRAV', 'ADPOPT', 'TMID']
            main_types = ['A', 'A', 'A', 'A', 'I', 'I', 'A', 'A']
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in main_cols]) + "\n")
            line_parts = [self.parser.format_field(pid, 'A')]
            for i, col in enumerate(main_cols[1:]):
                line_parts.append(self.parser.format_field(
                    main[col][idx], main_types[i + 1]))
            file_obj.write("".join(line_parts).rstrip() + "\n")

            active_options = {opt.upper() for opt in self.options}

            # Inertia
            if 'INERTIA' in active_options and inertia is not None:
                inertia_idx = np.where(inertia['PID'] == pid)[0]
                if inertia_idx.size > 0:
                    iidx = inertia_idx[0]
                    cols3 = ['XC', 'YC', 'ZC', 'TM', 'IRCS', 'NODEID']
                    types3 = ['F', 'F', 'F', 'F', 'I', 'I']
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols3]) + "\n")
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols3, types3)]).rstrip() + "\n")

                    cols4 = ['IXX', 'IXY', 'IXZ', 'IYY', 'IYZ', 'IZZ']
                    types4 = ['F'] * 6
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols4]) + "\n")
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols4, types4)]).rstrip() + "\n")

                    cols5 = ['VTX', 'VTY', 'VTZ', 'VRX', 'VRY', 'VRZ']
                    types5 = ['F'] * 6
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols5]) + "\n")
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols5, types5)]).rstrip() + "\n")
                    if inertia['IRCS'][iidx] == 1:
                        cols6 = ['XL', 'YL', 'ZL',
                                 'XLIP', 'YLIP', 'ZLIP', 'CID']
                        types6 = ['F', 'F', 'F', 'F', 'F', 'F', 'I']
                        file_obj.write(
                            "$#" + "".join([f"{col.lower():>10}" for col in cols6]) + "\n")
                        file_obj.write("".join([self.parser.format_field(inertia.get(
                            c, [None] * n_parts)[iidx], t) for c, t in zip(cols6, types6)]).rstrip() + "\n")

            # Reposition
            if 'REPOSITION' in active_options and reposition is not None:
                repo_idx = np.where(reposition['PID'] == pid)[0]
                if repo_idx.size > 0:
                    ridx = repo_idx[0]
                    cols = ['CMSN', 'MDEP', 'MOVOPT']
                    types = ['I'] * 3
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                    file_obj.write("".join([self.parser.format_field(
                        reposition[c][ridx], t) for c, t in zip(cols, types)]).rstrip() + "\n")

            # Contact
            if 'CONTACT' in active_options and contact is not None:
                contact_idx = np.where(contact['PID'] == pid)[0]
                if contact_idx.size > 0:
                    cidx = contact_idx[0]
                    cols = ['FS', 'FD', 'DC', 'VC',
                            'OPTT', 'SFT', 'SSF', 'CPARM8']
                    types = ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F']
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                    file_obj.write("".join([self.parser.format_field(
                        contact[c][cidx], t) for c, t in zip(cols, types)]).rstrip() + "\n")

            # Print
            if 'PRINT' in active_options and print_card is not None:
                print_idx = np.where(print_card['PID'] == pid)[0]
                if print_idx.size > 0:
                    pidx = print_idx[0]
                    file_obj.write("$#" + f"{'prbf':>10}\n")
                    file_obj.write(self.parser.format_field(
                        print_card['PRBF'][pidx], 'F').rstrip() + "\n")

            # Attachment Nodes
            if 'ATTACHMENT_NODES' in active_options and attachment_nodes is not None:
                attach_idx = np.where(attachment_nodes['PID'] == pid)[0]
                if attach_idx.size > 0:
                    aidx = attach_idx[0]
                    file_obj.write("$#" + f"{'ansid':>10}\n")
                    file_obj.write(self.parser.format_field(
                        attachment_nodes['ANSID'][aidx], 'I').rstrip() + "\n")

            # Field
            if 'FIELD' in active_options and field is not None:
                field_idx = np.where(field['PID'] == pid)[0]
                if field_idx.size > 0:
                    fidx = field_idx[0]
                    file_obj.write("$#" + f"{'fidbo':>10}\n")
                    file_obj.write(self.parser.format_field(
                        field['FIDBO'][fidx], 'I').rstrip() + "\n")
