"""Implementation of the *PART keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


def _pid_key(card: str) -> CardField:
    """The PID column that joins an optional card back to its part.

    Not a column of the file: *PART repeats its optional cards per part, and
    the parser adds this key so each optional card can be matched to the part
    it belongs to.
    """
    return CardField("PID", "A", width=10,
                     description=f"Part ID this {card} card belongs to "
                                 f"(join key added by the parser, not a "
                                 f"column of the file)")


class Part(LSDynaKeyword):
    """
    Implements the *PART keyword.
    """
    keyword_string = "*PART"

    description = (
        "Defines a part: the combination of a section, a material and "
        "optionally an equation of state and hourglass definition, referenced "
        "by elements through their PID.  Options add rigid-body inertia, "
        "repositioning, per-part contact parameters and more."
    )
    manual_section = "Vol I, *PART"

    # This class writes from `cards` alone, so a hand-built *PART renders
    # correctly even though `write` is custom.  Two requirements when building
    # one, both verified by test_part_build.py:
    #
    #   * Every optional card carries a PID column, which is what matches its
    #     rows back to their parts.  The values must compare equal to those on
    #     Card 2; the row order need not match.
    #   * A keyword option applies to the whole block, so an optional card
    #     needs a row for *every* part.  Rows for only some parts write a block
    #     that no longer reads back as it was built.
    builds_from_cards = True

    # Declared for introspection only: _parse_raw_data and write are both
    # overridden, so the base class never consults this list.  Cards are named
    # for what they hold rather than by manual card number, because one stored
    # card can merge several cards of the file (see 'inertia').
    card_schemas = [
        CardSchema("Card 1", [
            _pid_key("heading"),
            CardField("HEADING", "A", width=70,
                      description="Heading for the part"),
        ], repeating=True,
           description="Part heading, one per part."),

        CardSchema("Card 2", [
            CardField("PID", "A", width=10,
                      description="Part ID; unique number or label",
                      required=True),
            CardField("SECID", "A", width=10,
                      description="Section ID defined in a *SECTION keyword",
                      required=True),
            CardField("MID", "A", width=10,
                      description="Material ID defined in the *MAT section",
                      required=True),
            CardField("EOSID", "A", width=10,
                      description="Equation of state ID defined in the *EOS "
                                  "section; non-zero only for solid elements "
                                  "using an equation of state"),
            CardField("HGID", "I", width=10,
                      description="Hourglass/bulk viscosity ID defined in the "
                                  "*HOURGLASS section; 0 uses the defaults"),
            CardField("GRAV", "I", width=10,
                      description="Flag to turn on gravity initialization per "
                                  "*LOAD_DENSITY_DEPTH",
                      choices={0: "initialize only if included in PSID",
                               1: "initialize irrespective of PSID"}),
            CardField("ADPOPT", "A", width=10,
                      description="Adaptive remeshing option for this part; "
                                  "see *CONTROL_ADAPTIVE"),
            CardField("TMID", "A", width=10,
                      description="Thermal material property ID defined in the "
                                  "*MAT_THERMAL section"),
        ], repeating=True,
           description="Part definition, one per part."),

        CardSchema("inertia", [
            _pid_key("inertia"),
            CardField("XC", "F", width=10,
                      description="Global x coordinate of the centre of mass; "
                                  "ignored if NODEID is defined",
                      units="length"),
            CardField("YC", "F", width=10,
                      description="Global y coordinate of the centre of mass",
                      units="length"),
            CardField("ZC", "F", width=10,
                      description="Global z coordinate of the centre of mass",
                      units="length"),
            CardField("TM", "F", width=10,
                      description="Translational mass", units="mass"),
            CardField("IRCS", "I", width=10,
                      description="Reference coordinate system of the inertia "
                                  "tensor",
                      choices={0: "global inertia tensor",
                               1: "local tensor given by the orientation vectors"}),
            CardField("NODEID", "I", width=10,
                      description="Node defining the CG of the rigid body; "
                                  "supersedes XC, YC and ZC"),
            CardField("IXX", "F", width=10,
                      description="xx component of the inertia tensor",
                      units="mass*length^2"),
            CardField("IXY", "F", width=10,
                      description="xy component of the inertia tensor",
                      units="mass*length^2"),
            CardField("IXZ", "F", width=10,
                      description="xz component of the inertia tensor",
                      units="mass*length^2"),
            CardField("IYY", "F", width=10,
                      description="yy component of the inertia tensor",
                      units="mass*length^2"),
            CardField("IYZ", "F", width=10,
                      description="yz component of the inertia tensor",
                      units="mass*length^2"),
            CardField("IZZ", "F", width=10,
                      description="zz component of the inertia tensor",
                      units="mass*length^2"),
            CardField("VTX", "F", width=10,
                      description="Initial translational velocity of the rigid "
                                  "body in the global x direction",
                      units="length/time"),
            CardField("VTY", "F", width=10,
                      description="Initial translational velocity in the "
                                  "global y direction",
                      units="length/time"),
            CardField("VTZ", "F", width=10,
                      description="Initial translational velocity in the "
                                  "global z direction",
                      units="length/time"),
            CardField("VRX", "F", width=10,
                      description="Initial rotational velocity about the "
                                  "global x axis",
                      units="1/time"),
            CardField("VRY", "F", width=10,
                      description="Initial rotational velocity about the "
                                  "global y axis",
                      units="1/time"),
            CardField("VRZ", "F", width=10,
                      description="Initial rotational velocity about the "
                                  "global z axis",
                      units="1/time"),
            CardField("XL", "F", width=10,
                      description="x coordinate of the local x axis "
                                  "(only when IRCS = 1)",
                      units="length"),
            CardField("YL", "F", width=10,
                      description="y coordinate of the local x axis "
                                  "(only when IRCS = 1)",
                      units="length"),
            CardField("ZL", "F", width=10,
                      description="z coordinate of the local x axis "
                                  "(only when IRCS = 1)",
                      units="length"),
            CardField("XLIP", "F", width=10,
                      description="x coordinate of a vector in the local x-y "
                                  "plane (only when IRCS = 1)",
                      units="length"),
            CardField("YLIP", "F", width=10,
                      description="y coordinate of a vector in the local x-y "
                                  "plane (only when IRCS = 1)",
                      units="length"),
            CardField("ZLIP", "F", width=10,
                      description="z coordinate of a vector in the local x-y "
                                  "plane (only when IRCS = 1)",
                      units="length"),
            CardField("CID", "I", width=10,
                      description="Local coordinate system ID, as an "
                                  "alternative to the two vectors "
                                  "(only when IRCS = 1)"),
        ], repeating=True,
           condition=lambda kw: kw.has_option('INERTIA'),
           condition_doc="only with the INERTIA option; the XL-CID fields are "
                         "present only for parts with IRCS = 1",
           description="Rigid-body inertia properties.  Merges Cards 3-6 of "
                       "the manual into one stored card."),

        CardSchema("reposition", [
            _pid_key("reposition"),
            CardField("CMSN", "I", width=10,
                      description="Rigid body ID of the master part"),
            CardField("MDEP", "I", width=10,
                      description="Flag for dependent movement"),
            CardField("MOVOPT", "I", width=10,
                      description="Flag to control the movement of the part"),
        ], repeating=True,
           condition=lambda kw: kw.has_option('REPOSITION'),
           condition_doc="only with the REPOSITION option",
           description="Repositioning data for deformable parts."),

        CardSchema("contact", [
            _pid_key("contact"),
            CardField("FS", "F", width=10,
                      description="Static coefficient of friction"),
            CardField("FD", "F", width=10,
                      description="Dynamic coefficient of friction"),
            CardField("DC", "F", width=10,
                      description="Exponential decay coefficient"),
            CardField("VC", "F", width=10,
                      description="Coefficient for viscous friction",
                      units="stress"),
            CardField("OPTT", "A", width=10,
                      description="Optional contact thickness",
                      units="length"),
            CardField("SFT", "F", width=10,
                      description="Scale factor for the contact thickness"),
            CardField("SSF", "F", width=10,
                      description="Scale factor on the contact surface "
                                  "stiffness"),
            CardField("CPARM8", "F", width=10,
                      description="Flag controlling how parts of the automatic "
                                  "general contact are treated"),
        ], repeating=True,
           condition=lambda kw: kw.has_option('CONTACT'),
           condition_doc="only with the CONTACT option",
           description="Per-part contact parameters."),

        CardSchema("print", [
            _pid_key("print"),
            CardField("PRBF", "F", width=10,
                      description="Print flag for the rbdout and matsum files",
                      choices={0.0: "write to both rbdout and matsum",
                               1.0: "write to rbdout only",
                               2.0: "write to matsum only",
                               3.0: "write to neither"}),
        ], repeating=True,
           condition=lambda kw: kw.has_option('PRINT'),
           condition_doc="only with the PRINT option",
           description="Per-part output suppression flag."),

        CardSchema("attachment_nodes", [
            _pid_key("attachment nodes"),
            CardField("ANSID", "I", width=10,
                      description="Attachment node set ID for a deformable "
                                  "part switched to rigid"),
        ], repeating=True,
           condition=lambda kw: kw.has_option('ATTACHMENT_NODES'),
           condition_doc="only with the ATTACHMENT_NODES option",
           description="Attachment node set for deformable-to-rigid switching."),

        CardSchema("field", [
            _pid_key("field"),
            CardField("FIDBO", "I", width=10,
                      description="Field boundary output ID"),
        ], repeating=True,
           condition=lambda kw: kw.has_option('FIELD'),
           condition_doc="only with the FIELD option",
           description="Field data for the part."),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parses the raw data for *PART."""
        headings, main_data, inertia_data, reposition_data, contact_data, print_data, attachment_nodes_data, field_data = [
        ], [], [], [], [], [], [], []

        # Lines are kept as they are.  Stripping them here would shift every
        # fixed-width column left by the width of the leading blanks, which
        # goes unnoticed only while every value is a single digit: with
        # SECID = 10 the shift runs the fields together and PID parses as the
        # string "7        1".  The heading is free text and is stripped where
        # it is read, below.
        card_lines = [line for line in raw_lines[1:]
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
            if self.has_option('INERTIA'):
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

            if self.has_option('REPOSITION'):
                if i >= len(card_lines):
                    break
                repo_card = self.parser.parse_line(
                    card_lines[i], ['I', 'I', 'I'])
                i += 1
                reposition_data.append(
                    {'PID': pid, 'CMSN': repo_card[0], 'MDEP': repo_card[1], 'MOVOPT': repo_card[2]})

            if self.has_option('CONTACT'):
                if i >= len(card_lines):
                    break
                contact_card = self.parser.parse_line(
                    card_lines[i], ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F'])
                i += 1
                contact_data.append({'PID': pid, 'FS': contact_card[0], 'FD': contact_card[1], 'DC': contact_card[2], 'VC': contact_card[3],
                                    'OPTT': contact_card[4], 'SFT': contact_card[5], 'SSF': contact_card[6], 'CPARM8': contact_card[7]})

            if self.has_option('PRINT'):
                if i >= len(card_lines):
                    break
                print_card = self.parser.parse_line(card_lines[i], ['F'])
                i += 1
                print_data.append({'PID': pid, 'PRBF': print_card[0]})

            if self.has_option('ATTACHMENT_NODES'):
                if i >= len(card_lines):
                    break
                attach_card = self.parser.parse_line(card_lines[i], ['I'])
                i += 1
                attachment_nodes_data.append(
                    {'PID': pid, 'ANSID': attach_card[0]})

            if self.has_option('FIELD'):
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
            file_obj.write(self.parser.format_header(main_cols))
            line_parts = [self.parser.format_field(pid, 'A')]
            for i, col in enumerate(main_cols[1:]):
                line_parts.append(self.parser.format_field(
                    main[col][idx], main_types[i + 1]))
            file_obj.write("".join(line_parts).rstrip() + "\n")

            # Inertia
            if self.has_option('INERTIA') and inertia is not None:
                inertia_idx = np.where(inertia['PID'] == pid)[0]
                if inertia_idx.size > 0:
                    iidx = inertia_idx[0]
                    cols3 = ['XC', 'YC', 'ZC', 'TM', 'IRCS', 'NODEID']
                    types3 = ['F', 'F', 'F', 'F', 'I', 'I']
                    file_obj.write(self.parser.format_header(cols3))
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols3, types3)]).rstrip() + "\n")

                    cols4 = ['IXX', 'IXY', 'IXZ', 'IYY', 'IYZ', 'IZZ']
                    types4 = ['F'] * 6
                    file_obj.write(self.parser.format_header(cols4))
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols4, types4)]).rstrip() + "\n")

                    cols5 = ['VTX', 'VTY', 'VTZ', 'VRX', 'VRY', 'VRZ']
                    types5 = ['F'] * 6
                    file_obj.write(self.parser.format_header(cols5))
                    file_obj.write("".join([self.parser.format_field(
                        inertia[c][iidx], t) for c, t in zip(cols5, types5)]).rstrip() + "\n")
                    if inertia['IRCS'][iidx] == 1:
                        cols6 = ['XL', 'YL', 'ZL',
                                 'XLIP', 'YLIP', 'ZLIP', 'CID']
                        types6 = ['F', 'F', 'F', 'F', 'F', 'F', 'I']
                        file_obj.write(self.parser.format_header(cols6))
                        file_obj.write("".join([self.parser.format_field(inertia.get(
                            c, [None] * n_parts)[iidx], t) for c, t in zip(cols6, types6)]).rstrip() + "\n")

            # Reposition
            if self.has_option('REPOSITION') and reposition is not None:
                repo_idx = np.where(reposition['PID'] == pid)[0]
                if repo_idx.size > 0:
                    ridx = repo_idx[0]
                    cols = ['CMSN', 'MDEP', 'MOVOPT']
                    types = ['I'] * 3
                    file_obj.write(self.parser.format_header(cols))
                    file_obj.write("".join([self.parser.format_field(
                        reposition[c][ridx], t) for c, t in zip(cols, types)]).rstrip() + "\n")

            # Contact
            if self.has_option('CONTACT') and contact is not None:
                contact_idx = np.where(contact['PID'] == pid)[0]
                if contact_idx.size > 0:
                    cidx = contact_idx[0]
                    cols = ['FS', 'FD', 'DC', 'VC',
                            'OPTT', 'SFT', 'SSF', 'CPARM8']
                    types = ['F', 'F', 'F', 'F', 'A', 'F', 'F', 'F']
                    file_obj.write(self.parser.format_header(cols))
                    file_obj.write("".join([self.parser.format_field(
                        contact[c][cidx], t) for c, t in zip(cols, types)]).rstrip() + "\n")

            # Print
            if self.has_option('PRINT') and print_card is not None:
                print_idx = np.where(print_card['PID'] == pid)[0]
                if print_idx.size > 0:
                    pidx = print_idx[0]
                    file_obj.write(self.parser.format_header(['prbf']))
                    file_obj.write(self.parser.format_field(
                        print_card['PRBF'][pidx], 'F').rstrip() + "\n")

            # Attachment Nodes
            if self.has_option('ATTACHMENT_NODES') and attachment_nodes is not None:
                attach_idx = np.where(attachment_nodes['PID'] == pid)[0]
                if attach_idx.size > 0:
                    aidx = attach_idx[0]
                    file_obj.write(self.parser.format_header(['ansid']))
                    file_obj.write(self.parser.format_field(
                        attachment_nodes['ANSID'][aidx], 'I').rstrip() + "\n")

            # Field
            if self.has_option('FIELD') and field is not None:
                field_idx = np.where(field['PID'] == pid)[0]
                if field_idx.size > 0:
                    fidx = field_idx[0]
                    file_obj.write(self.parser.format_header(['fidbo']))
                    file_obj.write(self.parser.format_field(
                        field['FIDBO'][fidx], 'I').rstrip() + "\n")
