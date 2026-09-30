"""Implementation of the *BOUNDARY_SPC_SET keyword."""

from typing import List, TextIO
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


def _dof(name: str, what: str) -> CardField:
    return CardField(name, "I", width=10,
                     description=f"Constraint on {what}",
                     choices={0: "free", 1: "constrained"})


class BoundarySpcSet(LSDynaKeyword):
    """Implements the *BOUNDARY_SPC_SET keyword.

    SET is one value of OPTION1 on *BOUNDARY_SPC_OPTION1_{OPTION2}_{OPTION3};
    OPTION2 is BIRTH_DEATH and OPTION3 is ID.  The block holds one Card 1 per
    node set.  With BIRTH_DEATH each Card 1 is followed by its own Card 2, so
    the two alternate; with ID a single ID card comes first and applies to
    every set in the block.
    """

    # Every accepted name is registered.  The options appear in the manual's
    # order, OPTION2 before OPTION3.
    keyword_string = "*BOUNDARY_SPC_SET"
    keyword_aliases = [
        "*BOUNDARY_SPC_SET_ID",
        "*BOUNDARY_SPC_SET_BIRTH_DEATH",
        "*BOUNDARY_SPC_SET_BIRTH_DEATH_ID",
    ]
    exact_match = True

    description = (
        "Constrains translational and rotational degrees of freedom of every "
        "node in a node set, optionally in a local coordinate system and "
        "between a birth and a death time."
    )
    manual_section = "Vol I, *BOUNDARY_SPC"

    # DEATH defaults to 1e20; without this a blank DEATH would be written
    # back as 0.
    blank_means_default = True

    _CARD_ID = CardSchema("Card ID", [
        CardField("ID", "I", width=10,
                  description="SPC set ID the node sets belong to; need not be "
                              "unique",
                  required=True),
        CardField("HEADING", "A", width=70, default="",
                  description="Optional descriptor written to the d3hsp and "
                              "spcforc files"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("ID"),
       condition_doc="only with the ID option; once, before the first Card 1",
       description="SPC set ID and heading.")

    _CARD_1 = CardSchema("Card 1", [
        CardField("NSID", "I", width=10,
                  description="Node set ID; see *SET_NODE", required=True),
        CardField("CID", "I", width=10,
                  description="Coordinate system ID; see "
                              "*DEFINE_COORDINATE_SYSTEM.  0 is the global "
                              "system"),
        _dof("DOFX", "translation in local x"),
        _dof("DOFY", "translation in local y"),
        _dof("DOFZ", "translation in local z"),
        _dof("DOFRX", "rotation about local x"),
        _dof("DOFRY", "rotation about local y"),
        _dof("DOFRZ", "rotation about local z"),
    ], repeating=True, write_header=True,
       description="One constrained node set per line.")

    _CARD_2 = CardSchema("Card 2", [
        CardField("BIRTH", "F", width=10, default=0.0,
                  description="Activation time; ignored during dynamic "
                              "relaxation",
                  units="time"),
        CardField("DEATH", "F", width=10, default=1.0e20,
                  description="Deactivation time; ignored during dynamic "
                              "relaxation",
                  units="time"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.has_option("BIRTH_DEATH"),
       condition_doc="only with the BIRTH_DEATH option; one line after each "
                     "Card 1 line, with one row per Card 1 row",
       description="Birth and death time of the constraint.")

    # _parse_raw_data and write are both overridden, because the ID card is
    # read once before the interleaved Card 1 / Card 2 rows.  Declared for
    # introspection.
    card_schemas = [_CARD_ID, _CARD_1, _CARD_2]

    def _row_schemas(self) -> List[CardSchema]:
        """The cards making up one constrained set, in file order."""
        if self.has_option("BIRTH_DEATH"):
            return [self._CARD_1, self._CARD_2]
        return [self._CARD_1]

    def _parse_raw_data(self, raw_lines: List[str]):
        lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
        # Trailing blank lines only separate this keyword from the next.
        # Interior ones are kept: a blank Card 2 means the default times.
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return

        if self.has_option("ID"):
            self.cards["Card ID"] = self._parse_single_card(
                lines[0], self._CARD_ID)
            lines = lines[1:]

        schemas = self._row_schemas()
        self._parse_grouped_lines(lines, schemas)

        # A final Card 2 that was blank was dropped with the trailing blank
        # lines above; restore it with the default times so that every
        # Card 1 row keeps its Card 2 row.
        if self.has_option("BIRTH_DEATH"):
            n_sets = len(self.cards["Card 1"]["NSID"])
            n_times = len(self.cards["Card 2"]["BIRTH"])
            if n_times < n_sets:
                padded = self._parse_repeating_card(
                    [""] * (n_sets - n_times), self._CARD_2)
                for name, col in padded.items():
                    self.cards["Card 2"][name] = np.concatenate(
                        [self.cards["Card 2"][name], col])

    def write(self, file_obj: TextIO):
        self._write_keyword_line(file_obj)
        card_id = self.cards.get("Card ID")
        if card_id is not None:
            self._write_card(file_obj, card_id, self._CARD_ID)
        if "Card 1" in self.cards:
            self._write_grouped_schemas(file_obj, self._row_schemas())
