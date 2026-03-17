"""Edge case tests (Phase 5b).

Covers:
- Empty keyword (header line only, no data)
- UNKNOWN keyword roundtrip — content preserved verbatim
- Malformed data line — logs error, does not crash, adjacent keywords still parse
- Partial data line — missing fields filled with defaults
- Comment-only block — no crash
"""

import logging
import pytest
import sys
sys.path.append('.')

from dynakw import DynaKeywordReader
from dynakw.keywords.UNKNOWN import Unknown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(content: str, tmp_path) -> list:
    """Write *content* to a temp file, parse it, return list of keywords."""
    f = tmp_path / "input.k"
    f.write_text(content)
    return list(DynaKeywordReader(str(f)).keywords())


def _roundtrip(content: str, tmp_path) -> str:
    """Parse *content* then write back; return the written text."""
    in_f  = tmp_path / "input.k"
    out_f = tmp_path / "output.k"
    in_f.write_text(content)
    dkw = DynaKeywordReader(str(in_f))
    dkw.write(str(out_f))
    return out_f.read_text()


# ---------------------------------------------------------------------------
# Empty keyword
# ---------------------------------------------------------------------------

class TestEmptyKeyword:

    def test_node_no_data_parses(self, tmp_path):
        """*NODE with no data lines produces an empty Card 1, not an error."""
        kws = _parse("*NODE\n", tmp_path)
        assert len(kws) == 1
        card = kws[0].cards.get("Card 1", {})
        assert len(card.get("NID", [])) == 0

    def test_node_no_data_writes(self, tmp_path):
        """*NODE with no data round-trips to a file containing the keyword line."""
        out = _roundtrip("*NODE\n", tmp_path)
        assert "*NODE" in out

    def test_mat_elastic_no_data_parses(self, tmp_path):
        """*MAT_ELASTIC with no data lines produces empty cards, not an error."""
        kws = _parse("*MAT_ELASTIC\n", tmp_path)
        assert len(kws) == 1
        assert kws[0].cards == {}

    def test_mat_elastic_no_data_writes(self, tmp_path):
        """*MAT_ELASTIC with no data writes back only the keyword line."""
        out = _roundtrip("*MAT_ELASTIC\n", tmp_path)
        assert "*MAT_ELASTIC" in out

    def test_comment_only_block(self, tmp_path):
        """A keyword block whose data lines are all comments does not crash."""
        content = "*NODE\n$ this is a comment\n$ another comment\n"
        kws = _parse(content, tmp_path)
        assert len(kws) == 1
        assert "*NODE" in kws[0].full_keyword


# ---------------------------------------------------------------------------
# UNKNOWN keyword roundtrip
# ---------------------------------------------------------------------------

class TestUnknownRoundtrip:

    def test_unknown_parses_as_unknown(self, tmp_path):
        """Unrecognized keyword is stored as Unknown."""
        kws = _parse("*CONTROL_TERMINATION\n    0.100000\n", tmp_path)
        assert len(kws) == 1
        assert isinstance(kws[0], Unknown)

    def test_unknown_data_preserved(self, tmp_path):
        """Data lines of an unknown keyword are preserved in the output."""
        content = "*CONTROL_TERMINATION\n    0.100000\n"
        out = _roundtrip(content, tmp_path)
        assert "0.100000" in out

    def test_unknown_comment_preserved(self, tmp_path):
        """Comment lines inside an unknown keyword block are preserved."""
        content = "*CONTROL_TERMINATION\n$ end time = 0.1\n    0.100000\n"
        out = _roundtrip(content, tmp_path)
        assert "end time" in out
        assert "0.100000" in out

    def test_unknown_multiple_data_lines(self, tmp_path):
        """All data lines of an unknown keyword survive the roundtrip."""
        lines = ["    1.0  2.0", "    3.0  4.0", "    5.0  6.0"]
        content = "*MY_CUSTOM_KEYWORD\n" + "\n".join(lines) + "\n"
        out = _roundtrip(content, tmp_path)
        for line in lines:
            assert line.strip() in out

    def test_unknown_does_not_block_adjacent_known(self, tmp_path):
        """An unknown keyword between two known keywords does not prevent parsing."""
        content = (
            "*NODE\n"
            "1, 1.0, 2.0, 3.0\n"
            "*CONTROL_TERMINATION\n"
            "    0.100000\n"
            "*NODE\n"
            "2, 4.0, 5.0, 6.0\n"
        )
        kws = _parse(content, tmp_path)
        assert len(kws) == 3

        node_kws    = [k for k in kws if k.full_keyword == "*NODE"]
        unknown_kws = [k for k in kws if isinstance(k, Unknown)]
        assert len(node_kws) == 2
        assert len(unknown_kws) == 1

        assert 1 in node_kws[0].cards["Card 1"]["NID"]
        assert 2 in node_kws[1].cards["Card 1"]["NID"]


# ---------------------------------------------------------------------------
# Malformed / partial data lines
# ---------------------------------------------------------------------------

class TestMalformedData:

    def test_partial_line_fills_defaults(self, tmp_path):
        """Node line with only NID+XYZ (missing TC, RC) fills TC=RC=0."""
        # NODE fields: NID(8) X(16) Y(16) Z(16) TC(8) RC(8)
        # Comma-separated so field widths don't matter
        content = "*NODE\n1, 1.0, 2.0, 3.0\n"
        kws = _parse(content, tmp_path)
        card = kws[0].cards["Card 1"]
        assert int(card["NID"][0]) == 1
        assert int(card["TC"][0]) == 0
        assert int(card["RC"][0]) == 0

    def test_partial_line_multiple_nodes(self, tmp_path):
        """Multiple short node lines are all parsed; missing fields default to 0."""
        content = "*NODE\n1, 0.0, 0.0, 0.0\n2, 1.0, 0.0, 0.0\n3, 0.0, 1.0, 0.0\n"
        kws = _parse(content, tmp_path)
        card = kws[0].cards["Card 1"]
        assert len(card["NID"]) == 3
        assert list(card["NID"]) == [1, 2, 3]

    def test_wrong_type_does_not_crash(self, tmp_path, caplog):
        """A data line with text where a number is expected logs an error but does not raise."""
        # "foo bar baz" can't be parsed as NODE integers/floats;
        # the keyword block will fail and be logged as an error.
        content = "*NODE\nfoo bar baz\n"
        with caplog.at_level(logging.ERROR, logger="dynakw"):
            kws = _parse(content, tmp_path)
        # Should not raise; at least one keyword is returned (possibly Unknown)
        assert len(kws) >= 1

    def test_wrong_type_adjacent_keyword_unaffected(self, tmp_path):
        """A malformed keyword block does not prevent the next keyword from parsing."""
        content = (
            "*NODE\n"
            "foo bar baz\n"
            "*MAT_ELASTIC\n"
            "         1    7850.0  2.1E+11      0.30\n"
        )
        kws = _parse(content, tmp_path)
        assert len(kws) == 2
        # The MAT_ELASTIC block must have parsed correctly
        mat_kws = [k for k in kws if "*MAT_ELASTIC" in k.full_keyword
                   and not isinstance(k, Unknown)]
        assert len(mat_kws) == 1
        assert float(kws[1].cards["Card 1"]["E"][0]) == pytest.approx(2.1e11)
