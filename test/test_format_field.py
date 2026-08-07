"""Fixed-width float formatting.

A fixed-point rendering can fail in two directions, and only one of them is
visible to a "does it fit" test:

* ``%.4f`` of 2.1e11 is too long for a ten-character field, and
* ``%.4f`` of 7.85e-9 is ``"0.0000"`` --- short, and worthless.

The second wrote a steel density as zero.  These tests pin both directions, and
the requirement that ordinary values keep their conventional look.
"""

import pytest
import sys
sys.path.append('.')

from dynakw.utils.format_parser import FormatParser


@pytest.fixture
def fp():
    return FormatParser()


def _written(fp, value, width=10, long_format=False):
    return fp.format_field(value, "F", long_format=long_format, field_len=width)


# ---------------------------------------------------------------------------
# The bug: small magnitudes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    7.85e-9,        # steel density in mm-tonne-s, the motivating case
    1.254e-6,
    2.5e-5,
    1.254e-4,
    -7.85e-9,
    1e-300,
])
def test_small_values_are_not_flattened_to_zero(fp, value):
    written = _written(fp, value)
    assert float(written) != 0.0, f"{value} written as {written!r}"


@pytest.mark.parametrize("value", [7.85e-9, 1.254e-6, 2.5e-5, 1.254e-4])
def test_small_values_round_trip_exactly(fp, value):
    assert float(_written(fp, value)) == value


def test_a_value_too_small_for_the_decimals_switches_notation(fp):
    """%.4f cannot hold 1.254e-4: it has four decimals, so it writes 0.0001."""
    assert _written(fp, 1.254e-4).strip() == "1.254E-04"


# ---------------------------------------------------------------------------
# Ordinary values keep their conventional form
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    (0.0, "0.0000"),
    (1.0, "1.0000"),
    (0.3, "0.3000"),
    (-0.5, "-0.5000"),
    (0.001, "0.0010"),
    (1234.5, "1234.5000"),
    (1 / 3, "0.3333"),          # loses a little, but within what %.4f offers
])
def test_ordinary_values_stay_fixed_point(fp, value, expected):
    assert _written(fp, value).strip() == expected


def test_zero_is_written_as_zero(fp):
    assert _written(fp, 0.0).strip() == "0.0000"
    assert float(_written(fp, 0.0)) == 0.0


# ---------------------------------------------------------------------------
# Large magnitudes, which already worked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    (2.1e11, "2.100E+11"),
    (210000000000.0, "2.100E+11"),
    (1e300, "1.00E+300"),
])
def test_large_values_keep_their_previous_rendering(fp, value, expected):
    assert _written(fp, value).strip() == expected


# ---------------------------------------------------------------------------
# Wide fields keep the digits they have room for
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    7.13000011,        # a *DEFINE_CURVE ordinate, in a 20-character field
    13.5200005,
    -21.93931007,      # a *NODE coordinate, in a 16-character field
    29.07068825,
    -6.666666508,
    9.199999809,
])
@pytest.mark.parametrize("width", [16, 20])
def test_wide_fields_keep_the_whole_value(fp, value, width):
    """Four decimals in a twenty-character field throws away digits.

    A curve ordinate of 7.13000011 used to be written 7.1300, and a node
    coordinate of -21.93931007 as -21.9393 --- four significant digits of a
    mesh coordinate, lost on an ordinary read and write.
    """
    assert float(_written(fp, value, width)) == value


def test_a_wide_field_does_not_pad_with_noise(fp):
    """The extra decimals are only kept when they carry something.

    Otherwise every value would grow a tail of zeros: 7.13 would be written
    7.13000000000000 in a twenty-character field.
    """
    assert _written(fp, 7.13, 20).strip() == "7.1300"
    assert _written(fp, 0.1, 20).strip() == "0.1000"
    assert _written(fp, 23.0, 16).strip() == "23.0000"


@pytest.mark.parametrize("value,expected", [
    (0.3, "0.3000"),
    (1 / 3, "0.3333"),
    (7.13000011, "7.1300"),
    (-21.93931007, "-21.9393"),
])
def test_the_ten_character_field_is_unchanged(fp, value, expected):
    """The usual field has no room to spare, so its rendering is untouched."""
    assert _written(fp, value, 10).strip() == expected


# ---------------------------------------------------------------------------
# Field discipline
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [7.85e-9, 2.1e11, 0.3, -7.85e-9, 1e300, 0.0])
@pytest.mark.parametrize("width", [8, 10, 16, 20])
def test_output_never_exceeds_the_field(fp, value, width):
    assert len(_written(fp, value, width)) == width


def test_scientific_notation_leaves_a_separating_column(fp):
    """Filling the field runs one value into the next.

    A full-width 2.1000E+11 beside 7.8500 reads as "7.85002.1000E+11", which is
    still valid fixed-format input but unreadable.
    """
    pair = _written(fp, 7.85) + _written(fp, 2.1e11)
    assert pair == "    7.8500 2.100E+11"


def test_narrow_fields_still_beat_zero(fp):
    """Eight-character fields, as on *ELEMENT_SOLID's ortho card."""
    written = _written(fp, 7.85e-9, width=8)
    assert len(written) == 8
    assert float(written) != 0.0
    assert abs(float(written) - 7.85e-9) / 7.85e-9 < 0.01


def test_long_format_uses_six_decimals(fp):
    assert _written(fp, 0.5, width=20, long_format=True).strip() == "0.500000"


def test_long_format_also_rescues_small_values(fp):
    written = _written(fp, 7.85e-9, width=20, long_format=True)
    assert float(written) == 7.85e-9


# ---------------------------------------------------------------------------
# Through a full write / read cycle
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [7.85e-9, 1.254e-6, 0.3, 2.1e11, 0.0, -1.5e-7])
def test_values_survive_a_parse_of_what_was_written(fp, value):
    line = _written(fp, value)
    assert fp.parse_line(line, ["F"], field_len=[10])[0] == value


def test_a_material_density_survives_a_keyword_round_trip():
    """The case that started this: reading a deck and writing it back.

    *MAT_ELASTIC with a mm-tonne-s density used to come back as zero.
    """
    import io
    from dynakw.keywords.MAT_ELASTIC import MatElastic

    src = ["*MAT_ELASTIC", "         1 7.85E-09  210000.0       0.3"]
    kw = MatElastic(src[0], src)
    assert kw.cards["Card 1"]["RO"][0] == 7.85e-9

    buf = io.StringIO()
    kw.write(buf)
    lines = buf.getvalue().splitlines()
    again = MatElastic(lines[0], lines)

    assert again.cards["Card 1"]["RO"][0] == 7.85e-9
    assert again.cards["Card 1"]["E"][0] == 210000.0
    assert again.cards["Card 1"]["PR"][0] == 0.3
