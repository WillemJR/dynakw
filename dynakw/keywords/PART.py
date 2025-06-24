"""Implementation of the *PART keyword."""

from typing import TextIO, List
import pandas as pd
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.enums import KeywordType


class Part(LSDynaKeyword):
    """
    Implements the *PART keyword.
    """

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        if self.keyword_type != KeywordType.PART:
            pass

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parses the raw data for *PART."""
        active_options = {opt.upper() for opt in self.options}

        headings, main_data, inertia_data, reposition_data, contact_data, print_data, attachment_nodes_data, field_data = [], [], [], [], [], [], [], []

        card_lines = [line.strip() for line in raw_lines[1:] if not line.startswith('$') ]

        if not card_lines:
            return

        i = 0
        while i < len(card_lines):
            # Card 1: HEADING
            heading = card_lines[i].strip()
            i += 1
            if i >= len(card_lines): break

            # Card 2: Main Definition
            main_fields = self.parser.parse_line(card_lines[i], ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'])
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
                if i + 2 >= len(card_lines): break
                inertia_card3 = self.parser.parse_line(card_lines[i], ['F', 'F', 'F', 'F', 'I', 'I'])
                inertia_card4 = self.parser.parse_line(card_lines[i+1], ['F', 'F', 'F', 'F', 'F', 'F'])
                inertia_card5 = self.parser.parse_line(card_lines[i+2], ['F', 'F', 'F', 'F', 'F', 'F'])
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
                    if i >= len(card_lines): break
                    inertia_card6 = self.parser.parse_line(card_lines[i], ['F', 'F', 'F', 'F', 'F', 'F', 'I'])
                    i += 1
                    inertia_record.update({
                        'XL': inertia_card6[0], 'YL': inertia_card6[1], 'ZL': inertia_card6[2],
                        'XLIP': inertia_card6[3], 'YLIP': inertia_card6[4], 'ZLIP': inertia_card6[5],
                        'CID': inertia_card6[6]
                    })
                inertia_data.append(inertia_record)

            if 'REPOSITION' in active_options:
                if i >= len(card_lines): break
                repo_card = self.parser.parse_line(card_lines[i], ['I', 'I', 'I'])
                i += 1
                reposition_data.append({'PID': pid, 'CMSN': repo_card[0], 'MDEP': repo_card[1], 'MOVOPT': repo_card[2]})

            if 'CONTACT' in active_options:
                if i >= len(card_lines): break
                contact_card = self.parser.parse_line(card_lines[i], ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F'])
                i += 1
                contact_data.append({'PID': pid, 'FS': contact_card[0], 'FD': contact_card[1], 'DC': contact_card[2], 'VC': contact_card[3], 'OPTT': contact_card[4], 'SFT': contact_card[5], 'SSF': contact_card[6], 'CPARM8': contact_card[7]})

            if 'PRINT' in active_options:
                if i >= len(card_lines): break
                print_card = self.parser.parse_line(card_lines[i], ['F'])
                i += 1
                print_data.append({'PID': pid, 'PRBF': print_card[0]})

            if 'ATTACHMENT_NODES' in active_options:
                if i >= len(card_lines): break
                attach_card = self.parser.parse_line(card_lines[i], ['I'])
                i += 1
                attachment_nodes_data.append({'PID': pid, 'ANSID': attach_card[0]})

            if 'FIELD' in active_options:
                if i >= len(card_lines): break
                field_card = self.parser.parse_line(card_lines[i], ['I'])
                i += 1
                field_data.append({'PID': pid, 'FIDBO': field_card[0]})

        if headings:
            self.cards['Card 1'] = pd.DataFrame(headings).set_index('PID')
        if main_data:
            self.cards['Card 2'] = pd.DataFrame(main_data).set_index('PID')
        if inertia_data:
            self.cards['inertia'] = pd.DataFrame(inertia_data).set_index('PID')
        if reposition_data:
            self.cards['reposition'] = pd.DataFrame(reposition_data).set_index('PID')
        if contact_data:
            self.cards['contact'] = pd.DataFrame(contact_data).set_index('PID')
        if print_data:
            self.cards['print'] = pd.DataFrame(print_data).set_index('PID')
        if attachment_nodes_data:
            self.cards['attachment_nodes'] = pd.DataFrame(attachment_nodes_data).set_index('PID')
        if field_data:
            self.cards['field'] = pd.DataFrame(field_data).set_index('PID')

    def write(self, file_obj: TextIO):
        """Writes the *PART keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        main_df = self.cards.get("Card 2")
        if main_df is None or main_df.empty:
            return

        headings_df = self.cards.get("Card 1")
        inertia_df = self.cards.get("inertia")
        reposition_df = self.cards.get("reposition")
        contact_df = self.cards.get("contact")
        print_df = self.cards.get("print")
        attachment_nodes_df = self.cards.get("attachment_nodes")
        field_df = self.cards.get("field")

        for pid, row in main_df.iterrows():
            if headings_df is not None and pid in headings_df.index:
                file_obj.write(f"{headings_df.loc[pid]['HEADING']}\n")

            main_cols = ['SECID', 'MID', 'EOSID', 'HGID', 'GRAV', 'ADPOPT', 'TMID']
            main_types = ['A', 'A', 'A', 'A', 'I', 'I', 'A']
            line_parts = [self.parser.format_field(pid, 'A')]
            for col, ftype in zip(main_cols, main_types):
                line_parts.append(self.parser.format_field(row.get(col), ftype))
            file_obj.write("".join(line_parts).rstrip() + "\n")

            active_options = {opt.upper() for opt in self.options}

            if 'INERTIA' in active_options and inertia_df is not None and pid in inertia_df.index:
                inertia_row = inertia_df.loc[pid]
                cols3 = ['XC', 'YC', 'ZC', 'TM', 'IRCS', 'NODEID']; types3 = ['F', 'F', 'F', 'F', 'I', 'I']
                file_obj.write("".join([self.parser.format_field(inertia_row.get(c), t) for c, t in zip(cols3, types3)]).rstrip() + "\n")
                cols4 = ['IXX', 'IXY', 'IXZ', 'IYY', 'IYZ', 'IZZ']; types4 = ['F'] * 6
                file_obj.write("".join([self.parser.format_field(inertia_row.get(c), t) for c, t in zip(cols4, types4)]).rstrip() + "\n")
                cols5 = ['VTX', 'VTY', 'VTZ', 'VRX', 'VRY', 'VRZ']; types5 = ['F'] * 6
                file_obj.write("".join([self.parser.format_field(inertia_row.get(c), t) for c, t in zip(cols5, types5)]).rstrip() + "\n")
                if inertia_row.get('IRCS') == 1:
                    cols6 = ['XL', 'YL', 'ZL', 'XLIP', 'YLIP', 'ZLIP', 'CID']; types6 = ['F', 'F', 'F', 'F', 'F', 'F', 'I']
                    file_obj.write("".join([self.parser.format_field(inertia_row.get(c), t) for c, t in zip(cols6, types6)]).rstrip() + "\n")

            if 'REPOSITION' in active_options and reposition_df is not None and pid in reposition_df.index:
                repo_row = reposition_df.loc[pid]
                cols = ['CMSN', 'MDEP', 'MOVOPT']; types = ['I'] * 3
                file_obj.write("".join([self.parser.format_field(repo_row.get(c), t) for c, t in zip(cols, types)]).rstrip() + "\n")

            if 'CONTACT' in active_options and contact_df is not None and pid in contact_df.index:
                contact_row = contact_df.loc[pid]
                cols = ['FS', 'FD', 'DC', 'VC', 'OPTT', 'SFT', 'SSF', 'CPARM8']; types = ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F']
                file_obj.write("".join([self.parser.format_field(contact_row.get(c), t) for c, t in zip(cols, types)]).rstrip() + "\n")

            if 'PRINT' in active_options and print_df is not None and pid in print_df.index:
                print_row = print_df.loc[pid]
                file_obj.write(self.parser.format_field(print_row.get('PRBF'), 'F').rstrip() + "\n")

            if 'ATTACHMENT_NODES' in active_options and attachment_nodes_df is not None and pid in attachment_nodes_df.index:
                attach_row = attachment_nodes_df.loc[pid]
                file_obj.write(self.parser.format_field(attach_row.get('ANSID'), 'I').rstrip() + "\n")

            if 'FIELD' in active_options and field_df is not None and pid in field_df.index:
                field_row = field_df.loc[pid]
                file_obj.write(self.parser.format_field(field_row.get('FIDBO'), 'I').rstrip() + "\n")
