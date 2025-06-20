"""Implementation of the *ELEMENT_SHELL keyword."""

from .lsdyna_keyword import LSDynaKeyword
from ..core.enums import DynaKeyword
from ..utils.format_parser import FormatParser


class ElementShell(LSDynaKeyword):
    """
    Represents the *ELEMENT_SHELL keyword in an LS-DYNA keyword file.

    This class handles all variants of the *ELEMENT_SHELL keyword, including
    options like THICKNESS, BETA, MCID, OFFSET, DOF, COMPOSITE, and
    COMPOSITE_LONG.
    """

    _keyword = DynaKeyword.ELEMENT_SHELL
    _repr_fields = ["eid", "pid"]

    def __init__(self):
        super().__init__()
        self.options = {}
        self.eid = 0
        self.pid = 0
        self.nodes = [0] * 8
        self.thicknesses = [0.0] * 8
        self.beta_or_mcid = 0.0
        self.offset = 0.0
        self.dof_nodes = [0] * 4
        self.composite_data = []
        self.composite_long_data = []

    def _parse_options(self, keyword_str):
        """Parses the keyword string to identify active options."""
        keyword_str = keyword_str.upper()
        self.options = {
            "THICKNESS": "THICKNESS" in keyword_str,
            "BETA": "BETA" in keyword_str,
            "MCID": "MCID" in keyword_str,
            "OFFSET": "OFFSET" in keyword_str,
            "DOF": "DOF" in keyword_str,
            "COMPOSITE": "COMPOSITE" in keyword_str and "LONG" not in keyword_str,
            "COMPOSITE_LONG": "COMPOSITE_LONG" in keyword_str,
        }

    def _parse(self, lines):
        """Parses the lines for the *ELEMENT_SHELL keyword."""
        # Card 1 (Required)
        if not lines:
            return
        card1_format = "iiiiiiii"
        card1_data = FormatParser.parse_card_line(lines.pop(0), card1_format)
        self.eid, self.pid = card1_data[0], card1_data[1]
        self.nodes = card1_data[2:10]

        has_midside_nodes = any(n != 0 for n in self.nodes[4:])

        # Card 2 (Conditional)
        if self.options.get("THICKNESS") or self.options.get("BETA") or self.options.get("MCID"):
            if not lines or lines[0].startswith('*'): return
            card2_format = "ffff f"
            card2_data = FormatParser.parse_card_line(lines.pop(0), card2_format)
            self.thicknesses[0:4] = card2_data[0:4]
            self.beta_or_mcid = card2_data[4]

            # Card 3 (Conditional)
            if has_midside_nodes:
                if not lines or lines[0].startswith('*'): return
                card3_format = "ffff"
                card3_data = FormatParser.parse_card_line(lines.pop(0), card3_format)
                self.thicknesses[4:8] = card3_data

        # Card 4 (Conditional)
        if self.options.get("OFFSET"):
            if not lines or lines[0].startswith('*'): return
            card4_format = "f"
            card4_data = FormatParser.parse_card_line(lines.pop(0), card4_format)
            self.offset = card4_data[0]

        # Card 5 (Conditional)
        if self.options.get("DOF"):
            if not lines or lines[0].startswith('*'): return
            card5_format = "iiii"
            card5_data = FormatParser.parse_card_line(lines.pop(0), card5_format)
            self.dof_nodes = card5_data

        # Cards 6+ (COMPOSITE)
        if self.options.get("COMPOSITE"):
            while lines and not lines[0].startswith('*'):
                if len(lines[0]) > 30 and lines[0][30:40].strip() in ('', '0', '0.0'):
                    card6_format = "ifffif"
                    self.composite_data.append(FormatParser.parse_card_line(lines.pop(0), card6_format))
                else:
                    break

        # Cards 7+ (COMPOSITE_LONG)
        if self.options.get("COMPOSITE_LONG"):
            while lines and not lines[0].startswith('*'):
                if len(lines[0]) > 30 and lines[0][30:40].strip() in ('', '0', '0.0'):
                    card7_format = "if fi"
                    self.composite_long_data.append(FormatParser.parse_card_line(lines.pop(0), card7_format))
                else:
                    break

    def _write(self):
        """Writes the keyword and its data to a list of strings.""" 
        lines = []

        # Build keyword string
        keyword = "*ELEMENT_SHELL"
        opts = []
        if self.options.get("THICKNESS"): opts.append("THICKNESS")
        if self.options.get("BETA"): opts.append("BETA")
        if self.options.get("MCID"): opts.append("MCID")
        if self.options.get("OFFSET"): opts.append("OFFSET")
        if self.options.get("DOF"): opts.append("DOF")
        if self.options.get("COMPOSITE"): opts.append("COMPOSITE")
        if self.options.get("COMPOSITE_LONG"): opts.append("COMPOSITE_LONG")
        if opts:
            keyword += "_" + "_".join(opts)
        lines.append(keyword)

        # Card 1
        card1_fields = [self.eid, self.pid] + self.nodes
        lines.append(FormatParser.format_card_line(card1_fields, "iiiiiiiiii"))

        has_midside_nodes = any(n != 0 for n in self.nodes[4:])

        # Card 2
        if self.options.get("THICKNESS") or self.options.get("BETA") or self.options.get("MCID"):
            card2_fields = self.thicknesses[0:4] + [self.beta_or_mcid]
            lines.append(FormatParser.format_card_line(card2_fields, "fffff"))

            # Card 3
            if has_midside_nodes:
                lines.append(FormatParser.format_card_line(self.thicknesses[4:8], "ffff"))

        # Card 4
        if self.options.get("OFFSET"):
            lines.append(FormatParser.format_card_line([self.offset], "f"))

        # Card 5
        if self.options.get("DOF"):
            lines.append(FormatParser.format_card_line(self.dof_nodes, "iiii"))

        # Cards 6+
        if self.options.get("COMPOSITE"):
            for comp_data in self.composite_data:
                lines.append(FormatParser.format_card_line(comp_data, "ifffif"))

        # Cards 7+
        if self.options.get("COMPOSITE_LONG"):
            for comp_long_data in self.composite_long_data:
                lines.append(FormatParser.format_card_line(comp_long_data, "if fi"))

        return lines

    @classmethod
    def from_keyword_and_lines(cls, keyword, lines):
        """Creates an ElementShell instance from a keyword and a list of lines."""
        instance = cls()
        instance._parse_options(keyword)
        instance._parse(lines)
        return instance
