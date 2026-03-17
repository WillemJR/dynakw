"""Implementation of the *ELEMENT_SHELL keyword."""

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ElementShell(LSDynaKeyword):
    """
    Implements the *ELEMENT_SHELL keyword.

    Handles options: THICKNESS, BETA, MCID, OFFSET, DOF, COMPOSITE, COMPOSITE_LONG.

    Card storage
    ------------
    Card 1  : EID, PID, N1-N8                 (int32, width=8)
    Card 2  : THIC1-4 + BETA or MCID          (float64/int32, width=16)
    Card 3  : THIC5-8 for midside nodes        (float64, width=16)
    Card 4  : OFFSET                           (float64, width=16)
    Card 5  : NS1-NS4 scalar nodes             (int32, width=8)
    Card 6  : Composite layers — 2D arrays     (n_elems × max_layers)
              Keys: MID (int32), THICK (float64), B (float64), N_LAYERS (int32)
    Card 7  : Composite-long layers — 2D arrays
              Keys: MID, THICK, B, PLYID, N_LAYERS
    """

    keyword_string = "*ELEMENT_SHELL"

    _CARD1_SCHEMA = CardSchema("Card 1", [
        CardField("EID", "I", width=8),
        CardField("PID", "I", width=8),
        CardField("N1",  "I", width=8),
        CardField("N2",  "I", width=8),
        CardField("N3",  "I", width=8),
        CardField("N4",  "I", width=8),
        CardField("N5",  "I", width=8),
        CardField("N6",  "I", width=8),
        CardField("N7",  "I", width=8),
        CardField("N8",  "I", width=8),
    ], repeating=True, write_header=True)

    _CARD2_THICKNESS = CardSchema("Card 2", [
        CardField("THIC1", "F", width=16),
        CardField("THIC2", "F", width=16),
        CardField("THIC3", "F", width=16),
        CardField("THIC4", "F", width=16),
    ], write_header=True)

    _CARD2_BETA = CardSchema("Card 2", [
        CardField("THIC1", "F", width=16),
        CardField("THIC2", "F", width=16),
        CardField("THIC3", "F", width=16),
        CardField("THIC4", "F", width=16),
        CardField("BETA",  "F", width=16),
    ], write_header=True)

    _CARD2_MCID = CardSchema("Card 2", [
        CardField("THIC1", "F", width=16),
        CardField("THIC2", "F", width=16),
        CardField("THIC3", "F", width=16),
        CardField("THIC4", "F", width=16),
        CardField("MCID",  "I", width=16),
    ], write_header=True)

    _CARD3_SCHEMA = CardSchema("Card 3", [
        CardField("THIC5", "F", width=16),
        CardField("THIC6", "F", width=16),
        CardField("THIC7", "F", width=16),
        CardField("THIC8", "F", width=16),
    ], write_header=True)

    _CARD4_SCHEMA = CardSchema("Card 4", [
        CardField("OFFSET", "F", width=16),
    ], write_header=True)

    _CARD5_SCHEMA = CardSchema("Card 5", [
        CardField("NS1", "I", width=8),
        CardField("NS2", "I", width=8),
        CardField("NS3", "I", width=8),
        CardField("NS4", "I", width=8),
    ], write_header=True)

    def _card2_schema(self, opts):
        if "BETA" in opts:
            return self._CARD2_BETA
        if "MCID" in opts:
            return self._CARD2_MCID
        return self._CARD2_THICKNESS

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [l for l in raw_lines[1:]
                      if l.strip() and not l.strip().startswith('$')]
        if not card_lines:
            return

        opts = {o.upper() for o in self.options}
        has_thickness = "THICKNESS" in opts
        has_beta      = "BETA"      in opts
        has_mcid      = "MCID"      in opts
        has_offset    = "OFFSET"    in opts
        has_dof       = "DOF"       in opts
        has_composite      = "COMPOSITE"      in opts
        has_composite_long = "COMPOSITE_LONG" in opts
        has_card2 = has_thickness or has_beta or has_mcid

        # Fast path: basic case — fully schema-driven
        if not any([has_card2, has_offset, has_dof, has_composite, has_composite_long]):
            self._parse_grouped_lines(card_lines, [self._CARD1_SCHEMA])
            return

        # General case: per-element loop
        s1 = self._CARD1_SCHEMA
        s2 = self._card2_schema(opts)
        s3 = self._CARD3_SCHEMA
        s5 = self._CARD5_SCHEMA

        def _parse(schema, line):
            return self.parser.parse_line(
                line, [f.type for f in schema.fields],
                field_len=[f.width for f in schema.fields])

        c1_rows, c2_rows, c3_rows = [], [], []
        c4_vals, c5_rows = [], []
        c6_all, c7_all = [], []   # list of per-element layer lists

        i = 0
        while i < len(card_lines):
            # Card 1
            v1 = _parse(s1, card_lines[i]); i += 1
            c1_rows.append(v1)
            has_mid = any(v1[j] is not None and int(v1[j]) > 0 for j in range(6, 10))

            # Card 2
            if has_card2 and i < len(card_lines):
                c2_rows.append(_parse(s2, card_lines[i])); i += 1

            # Card 3 — only for elements with midside nodes
            if has_mid and has_thickness and i < len(card_lines):
                c3_rows.append(_parse(s3, card_lines[i])); i += 1
            else:
                c3_rows.append(None)

            # Card 4
            if has_offset and i < len(card_lines):
                c4_vals.append(
                    self.parser.parse_line(card_lines[i], ["F"], field_len=[16])[0])
                i += 1

            # Card 5
            if has_dof and i < len(card_lines):
                c5_rows.append(_parse(s5, card_lines[i])); i += 1

            # Card 6 (COMPOSITE): two layers per line
            if has_composite:
                layers = []
                while i < len(card_lines):
                    v = self.parser.parse_line(
                        card_lines[i], ["I", "F", "F", "I", "F", "F"],
                        field_len=[10] * 6)
                    i += 1
                    layers.append((v[0], v[1], v[2]))
                    if v[3] is not None and int(v[3]) != 0:
                        layers.append((v[3], v[4], v[5]))
                c6_all.append(layers)

            # Card 7 (COMPOSITE_LONG): one layer per line
            if has_composite_long:
                layers = []
                while i < len(card_lines):
                    v = self.parser.parse_line(
                        card_lines[i], ["I", "F", "F", "I"],
                        field_len=[10] * 4)
                    i += 1
                    layers.append((v[0], v[1], v[2], v[3]))
                c7_all.append(layers)

        # --- Store Card 1 ---
        if c1_rows:
            arr = np.array(c1_rows, dtype=object)
            self.cards["Card 1"] = {
                f.name: arr[:, j].astype(self._DTYPE_MAP[f.type], copy=False)
                for j, f in enumerate(s1.fields)
            }

        # --- Store Card 2 ---
        if c2_rows:
            arr = np.array(c2_rows, dtype=object)
            self.cards["Card 2"] = {
                f.name: arr[:, j].astype(self._DTYPE_MAP[f.type], copy=False)
                for j, f in enumerate(s2.fields)
            }

        # --- Store Card 3 (padded with zeros for elements without midside nodes) ---
        if any(r is not None for r in c3_rows):
            padded = [r if r is not None else [0.0] * 4 for r in c3_rows]
            arr = np.array(padded, dtype=np.float64)
            self.cards["Card 3"] = {f.name: arr[:, j] for j, f in enumerate(s3.fields)}

        # --- Store Card 4 ---
        if c4_vals:
            self.cards["Card 4"] = {"OFFSET": np.array(c4_vals, dtype=np.float64)}

        # --- Store Card 5 ---
        if c5_rows:
            arr = np.array(c5_rows, dtype=object)
            self.cards["Card 5"] = {
                f.name: arr[:, j].astype(self._DTYPE_MAP[f.type], copy=False)
                for j, f in enumerate(s5.fields)
            }

        # --- Store Card 6 (COMPOSITE): 2D arrays (n_elems × max_layers) ---
        if c6_all:
            n = len(c6_all)
            max_l = max(len(ls) for ls in c6_all)
            mid_arr   = np.zeros((n, max_l), dtype=np.int32)
            thick_arr = np.zeros((n, max_l), dtype=np.float64)
            b_arr     = np.zeros((n, max_l), dtype=np.float64)
            n_layers  = np.zeros(n, dtype=np.int32)
            for ei, layers in enumerate(c6_all):
                n_layers[ei] = len(layers)
                for li, (mid, thick, b) in enumerate(layers):
                    mid_arr[ei, li]   = 0   if mid   is None else int(mid)
                    thick_arr[ei, li] = 0.0 if thick is None else float(thick)
                    b_arr[ei, li]     = 0.0 if b     is None else float(b)
            self.cards["Card 6"] = {
                "MID": mid_arr, "THICK": thick_arr, "B": b_arr,
                "N_LAYERS": n_layers,
            }

        # --- Store Card 7 (COMPOSITE_LONG): 2D arrays ---
        if c7_all:
            n = len(c7_all)
            max_l = max(len(ls) for ls in c7_all)
            mid_arr   = np.zeros((n, max_l), dtype=np.int32)
            thick_arr = np.zeros((n, max_l), dtype=np.float64)
            b_arr     = np.zeros((n, max_l), dtype=np.float64)
            plyid_arr = np.zeros((n, max_l), dtype=np.int32)
            n_layers  = np.zeros(n, dtype=np.int32)
            for ei, layers in enumerate(c7_all):
                n_layers[ei] = len(layers)
                for li, (mid, thick, b, plyid) in enumerate(layers):
                    mid_arr[ei, li]   = 0   if mid   is None else int(mid)
                    thick_arr[ei, li] = 0.0 if thick is None else float(thick)
                    b_arr[ei, li]     = 0.0 if b     is None else float(b)
                    plyid_arr[ei, li] = 0   if plyid is None else int(plyid)
            self.cards["Card 7"] = {
                "MID": mid_arr, "THICK": thick_arr, "B": b_arr,
                "PLYID": plyid_arr, "N_LAYERS": n_layers,
            }

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        opts = {o.upper() for o in self.options}
        has_thickness      = "THICKNESS"      in opts
        has_beta           = "BETA"           in opts
        has_mcid           = "MCID"           in opts
        has_offset         = "OFFSET"         in opts
        has_dof            = "DOF"            in opts
        has_composite      = "COMPOSITE"      in opts
        has_composite_long = "COMPOSITE_LONG" in opts
        has_card2 = has_thickness or has_beta or has_mcid

        # Fast path: basic case
        if not any([has_card2, has_offset, has_dof, has_composite, has_composite_long]):
            card1 = self.cards.get("Card 1")
            if card1 is not None:
                self._write_card(file_obj, card1, self._CARD1_SCHEMA)
            return

        s2 = self._card2_schema(opts)

        # Write all headers first
        def _write_header(schema):
            file_obj.write(self.parser.format_header(
                [f.header_name or f.name for f in schema.fields],
                field_len=[f.width for f in schema.fields]))

        _write_header(self._CARD1_SCHEMA)
        if has_card2:
            _write_header(s2)
        if "Card 3" in self.cards and has_thickness:
            _write_header(self._CARD3_SCHEMA)
        if has_offset:
            _write_header(self._CARD4_SCHEMA)
        if has_dof:
            _write_header(self._CARD5_SCHEMA)
        if has_composite:
            file_obj.write(self.parser.format_header(
                ["mid1", "thick1", "b1", "mid2", "thick2", "b2"]))
        if has_composite_long:
            file_obj.write(self.parser.format_header(
                ["mid", "thick", "b", "plyid"]))

        card1 = self.cards.get("Card 1")
        if card1 is None:
            return

        n_elem = len(card1["EID"])
        card2 = self.cards.get("Card 2")
        card3 = self.cards.get("Card 3")
        card4 = self.cards.get("Card 4")
        card5 = self.cards.get("Card 5")
        card6 = self.cards.get("Card 6")
        card7 = self.cards.get("Card 7")

        for i in range(n_elem):
            # Card 1
            parts = [self.parser.format_field(card1[f.name][i], f.type, field_len=f.width)
                     for f in self._CARD1_SCHEMA.fields]
            file_obj.write(''.join(parts) + '\n')

            # Card 2
            if card2 is not None:
                parts = [self.parser.format_field(card2[f.name][i], f.type, field_len=f.width)
                         for f in s2.fields]
                file_obj.write(''.join(parts) + '\n')

            # Card 3 — only for elements with midside nodes
            if card3 is not None:
                has_mid = any(int(card1[f"N{j}"][i]) > 0 for j in range(5, 9))
                if has_mid:
                    parts = [self.parser.format_field(card3[f.name][i], f.type, field_len=f.width)
                             for f in self._CARD3_SCHEMA.fields]
                    file_obj.write(''.join(parts) + '\n')

            # Card 4
            if card4 is not None:
                file_obj.write(
                    self.parser.format_field(card4["OFFSET"][i], "F", field_len=16) + '\n')

            # Card 5
            if card5 is not None:
                parts = [self.parser.format_field(card5[f.name][i], f.type, field_len=f.width)
                         for f in self._CARD5_SCHEMA.fields]
                file_obj.write(''.join(parts) + '\n')

            # Card 6 (COMPOSITE): two layers per output line
            if card6 is not None:
                n_lay = int(card6["N_LAYERS"][i])
                for l in range(0, n_lay, 2):
                    parts = [
                        self.parser.format_field(card6["MID"][i, l],   "I"),
                        self.parser.format_field(card6["THICK"][i, l], "F"),
                        self.parser.format_field(card6["B"][i, l],     "F"),
                    ]
                    if l + 1 < n_lay:
                        parts += [
                            self.parser.format_field(card6["MID"][i, l+1],   "I"),
                            self.parser.format_field(card6["THICK"][i, l+1], "F"),
                            self.parser.format_field(card6["B"][i, l+1],     "F"),
                        ]
                    else:
                        parts += [self.parser.format_field(None, "I"),
                                  self.parser.format_field(None, "F"),
                                  self.parser.format_field(None, "F")]
                    file_obj.write(''.join(parts) + '\n')

            # Card 7 (COMPOSITE_LONG): one layer per output line
            if card7 is not None:
                n_lay = int(card7["N_LAYERS"][i])
                for l in range(n_lay):
                    parts = [
                        self.parser.format_field(card7["MID"][i, l],   "I"),
                        self.parser.format_field(card7["THICK"][i, l], "F"),
                        self.parser.format_field(card7["B"][i, l],     "F"),
                        self.parser.format_field(card7["PLYID"][i, l], "I"),
                    ]
                    file_obj.write(''.join(parts) + '\n')
