"""Abstract base class for all LS-DYNA keyword objects."""

from collections import OrderedDict
from abc import ABC, abstractmethod
from typing import TextIO, List, Dict, Optional, Tuple
import numpy as np
from dynakw.core.enums import KeywordType
from dynakw.core.card_schema import CardField, CardGroup, CardSchema
from dynakw.core.parameter_ref import ParameterRef
from dynakw.utils.format_parser import FormatParser
import os
import importlib


class LSDynaKeyword(ABC):
    """
    Base class for all LS-DYNA keyword objects.

    This class provides the basic structure for representing an LS-DYNA
    keyword, including methods for parsing from raw text and writing
    back to a file format.

    Subclasses can either:

    - Define ``card_schemas`` (a list of CardSchema objects) to get automatic
      parse and write behaviour provided by this base class, or
    - Override ``_parse_raw_data`` and ``write`` directly for custom logic.

    Attributes:
        cards ( Dict[str, Dict[str, np.ndarray]] = {} ): The cards content as described in the LS-DYNA manual; e.g. kw.cards['Card 1']['SF']
        title (Optional[str]): The title line of a ``_TITLE`` variant, or None.
            See :attr:`supports_title`.
    """

    KEYWORD_MAP: Dict[str, "LSDynaKeyword"] = OrderedDict()
    """A registry of all known keyword strings and the classes that handle them."""

    description: str = ""
    """What the keyword does, per the LS-DYNA manual.  One or two sentences.

    Reported by introspection, so a caller can tell what a keyword is for
    without opening the manual."""

    manual_section: str = ""
    """Where the keyword is documented, e.g. ``"Vol I, *NODE"``."""

    card_schemas: List[CardSchema] = []
    """Declarative card layout. Override in subclasses to enable auto-parse/write.

    Subclasses that override ``_parse_raw_data`` **and** ``write`` should still
    declare their schemas here.  The base implementations are the only consumers
    of this list, so populating it is inert for such a class — but it makes the
    card layout visible to introspection instead of hiding it in private
    attributes.  Use ``CardSchema.condition``/``condition_doc`` to record when
    each card applies, and ``CardSchema.dynamic`` for cards whose field list is
    determined by data parsed earlier in the keyword."""

    card_groups: List[CardGroup] = []
    """Grouped card layout for interleaved (per-element) parse/write.
    When set, each group is written as: all headers first, then one row per schema
    per element. Takes precedence over card_schemas in the default implementations."""

    builds_from_cards: bool = False
    """Whether this class writes correctly from a hand-populated ``cards`` dict.

    A class that uses the base ``write`` gets this for free: that writer renders
    purely from ``cards`` and the declared schemas, so introspection reports it
    as buildable without the flag.

    A class with its own ``write`` may expect keys or shapes the schemas do not
    describe, so it is reported as *not* buildable until someone checks.  Set
    this to True once the writer is known to render correctly from cards built
    to the schemas, and cover it with a test that builds an instance from data,
    writes it and reads it back --- the flag is a claim, and the test is the
    evidence for it.

    Setting it does not change any behaviour; it only changes what
    ``describe_keyword`` reports."""

    supports_title: bool = False
    """Whether this keyword accepts the ``TITLE`` option.

    Many LS-DYNA keywords do: the line immediately after the keyword line is
    then a free-form title (80a) rather than data.  The mechanics are handled
    here rather than per keyword --- when the option is in the keyword name, the
    title line is taken off the block before ``_parse_raw_data`` sees it and
    kept in :attr:`title`, and written back after the keyword line.  So a class
    that sets this needs no other change, and one that overrides
    ``_parse_raw_data`` still receives a block whose first line is the keyword
    line and whose second is Card 1.

    **Set it only where the manual says the option exists, and cite where.**
    The manual grants TITLE by family, in the introduction to a section rather
    than in each keyword's option list --- "an additional option TITLE may be
    appended to all the *SECTION keywords" (Vol I, *SECTION), and likewise for
    *SET, *DEFINE (bar *DEFINE_FUNCTION), *MAT, *EOS, *HOURGLASS and *SENSOR.
    Other families do not have it at all: *NODE, *ELEMENT, *PART, *CONTROL,
    *PARAMETER, *BOUNDARY and *CONSTRAINED list no TITLE among their options.
    Some of those have an ``ID`` option that reads an ID *and* a heading, which
    is a different card and not this.

    The default is False because of which way each mistake fails.  A wrong True
    silently eats the first data line of every such block and shifts every card
    up by one; a wrong False leaves a ``_TITLE`` block to fall through to
    ``Unknown``, which keeps it verbatim and says so in the log.  The flag is
    also what introspection reports as ``has_title``, so a deck generator asking
    whether it may put a title on a keyword gets an answer that was checked.

    ``Unknown`` must never set it: its block is written back verbatim, so
    nothing may be lifted out of it."""

    blank_means_default: bool = False
    """Whether a blank field is read as the ``default`` its CardField declares.

    By default a blank field parses as 0 whatever the schema says, so a field
    whose documented default is non-zero reads back as 0 and is written out as
    0.  LS-DYNA usually reads a blank numeric field as 0 too and then applies
    the default, so the two agree --- but not always: ``INITITR`` on the MPP
    card of *CONTACT is documented as "an input of 0 means 0, not the default
    value", and ``IGAP`` gives 0 a meaning distinct from its default of 1.

    Setting this makes the class read each blank field as its declared
    ``default``, so the value written back is the value LS-DYNA would have used
    for the blank.  That is only sound when every ``default`` in the class's
    schemas is right: a default that depends on context (the contact type, the
    SOFT option) must be left at 0 so that LS-DYNA still decides it.

    Opt-in, because turning it on for an existing keyword changes what that
    keyword writes."""

    exact_match: bool = False
    """Whether the keyword line must equal a registered name exactly.

    Keyword dispatch normally accepts the longest registered name that is a
    *prefix* of the keyword line, so that open-ended option suffixes
    (``*PART_INERTIA``, ``*BOUNDARY_PRESCRIBED_MOTION_RIGID``) reach the right
    class without every combination being registered.

    That is wrong when a longer, unrelated keyword happens to start with a
    registered name -- ``*MAT_ELASTIC_PLASTIC_HYDRO`` is MAT_010, not an option
    of ``*MAT_ELASTIC``.  Set ``exact_match = True`` on classes that register
    every valid name they accept via ``keyword_string``/``keyword_aliases``;
    a longer line is then treated as a different keyword and falls through to
    ``Unknown``, which preserves it verbatim instead of mis-parsing it."""

    def __init_subclass__(cls, **kwargs):
        """This method is called when a subclass of LSDynaKeyword is defined."""
        super().__init_subclass__(**kwargs)
        # The 'keyword_string' is the primary identifier for the keyword class.
        if hasattr(cls, 'keyword_string'):
            # Register the primary keyword string.
            cls.KEYWORD_MAP[cls.keyword_string] = cls
        # 'keyword_aliases' can be used for alternative names for the same keyword.
        if hasattr(cls, 'keyword_aliases'):
            for alias in cls.keyword_aliases:
                cls.KEYWORD_MAP[alias] = cls

    def __init__(self, keyword_name: str, raw_lines: List[str] = None, start_line: int = None):
        """
        Initializes the LSDynaKeyword object.

        Args:
            keyword_name (str): The full name of the keyword (e.g., ``*BOUNDARY_PRESCRIBED_MOTION_NODE``).
            raw_lines (List[str], optional): The raw text lines for the keyword. Defaults to None.
            start_line (int, optional): The line number where the keyword starts in the file. Defaults to None.
        """
        self.full_keyword = keyword_name.strip()
        self.type, self.options = self._parse_keyword_name(self.full_keyword)
        self.cards: Dict[str, Dict[str, np.ndarray]] = {}
        self.parser = FormatParser()
        self._start_line = start_line
        self.title: Optional[str] = None

        if raw_lines:
            self._parse_raw_data(self._extract_title(raw_lines))

    @staticmethod
    def _parse_keyword_name(keyword_name: str) -> Tuple[KeywordType, List[str]]:
        """
        Parses the keyword name to extract the base type and options.
        Example: "*BOUNDARY_PRESCRIBED_MOTION_NODE" -> (KeywordType.BOUNDARY_PRESCRIBED_MOTION, ["NODE"])
        """
        # Remove leading '*' and split by '_'
        parts = keyword_name.strip()[1:].split('_')

        # Find the longest matching enum name
        for i in range(len(parts), 0, -1):
            base_keyword_str = '_'.join(parts[:i])
            try:
                type = KeywordType[base_keyword_str]
                options = parts[i:]
                return type, options
            except KeyError:
                continue

        return KeywordType.UNKNOWN, parts

    @classmethod
    def resolve(cls, keyword_line: str) -> "Optional[type]":
        """The keyword class that handles *keyword_line*, or None.

        The longest registered name that is a *prefix* of the line wins, so
        open-ended option suffixes reach the right class without every
        combination being registered.  A class with ``exact_match`` set is only
        matched by a name it registers itself --- plus that name with
        ``_TITLE`` appended, which is the same keyword with a title card and not
        a different one.  Without that, ``*MAT_RIGID_TITLE`` would fall through
        to ``Unknown``, since the whole point of ``exact_match`` is that a
        longer line is a different keyword.

        This is the dispatch used when reading a file, and also how
        introspection decides which class a keyword name describes, so the two
        can never disagree about what a name means.

        Args:
            keyword_line: A keyword line, e.g. ``"*MAT_ELASTIC_FLUID"``.
                Leading and trailing whitespace and any trailing format
                modifiers (``+-%``) are ignored.

        Returns:
            The handling class, or None when nothing matches.
        """
        clean_line = keyword_line.strip().rstrip('+-% ').upper()

        best_match = None
        best_length = 0
        for keyword_str, keyword_class in cls.KEYWORD_MAP.items():
            if not clean_line.startswith(keyword_str):
                continue
            if keyword_class.exact_match and clean_line != keyword_str:
                titled = keyword_class.supports_title and \
                    clean_line == f"{keyword_str}_TITLE"
                if not titled:
                    continue
            if len(keyword_str) > best_length:
                best_match = keyword_class
                best_length = len(keyword_str)
        return best_match

    NEAR_MISS_TOKENS: int = 2
    """How many leading ``_``-separated tokens a registered name must share with
    an unresolved keyword line before the miss is reported as a near miss.

    One shared token is only the family word --- ``*CONTROL_TIMESTEP`` and
    ``*CONTROL_TERMINATION`` share ``CONTROL`` and are otherwise unrelated
    keywords, so one token would make every unimplemented member of an
    implemented family noisy.  Two means the registry already covers a name at
    the same level of qualification as the line, which is the shape a
    too-narrow registration has."""

    @classmethod
    def explain_unresolved(cls, keyword_line: str) -> Optional[str]:
        """Why *keyword_line* did not resolve, when that is worth reporting.

        :meth:`resolve` returning None has two very different causes, and only
        one of them is news:

        * The library has no class for the keyword at all.  Nothing is wrong ---
          ``Unknown`` keeps the block verbatim, which is the designed behaviour
          for the thousand-odd keywords that are not implemented.  Reported as
          None here, so the caller can log it at debug level.
        * The registry *nearly* covers the line.  Either a registered name is a
          prefix of it but the class sets ``exact_match``, or a registered name
          sits in the same family at the same depth without being a prefix.
          Both are the shape a registration mistake has, and both are also how
          a deliberate exclusion looks --- ``*MAT_ELASTIC_PLASTIC_HYDRO`` is
          rejected on purpose.  They are indistinguishable from here, so this
          reports them and leaves the judgement to whoever reads the log.

        Args:
            keyword_line: A keyword line, cleaned exactly as :meth:`resolve`
                cleans it.

        Returns:
            A message naming the closest registered keyword, or None when the
            line is simply an unimplemented keyword.
        """
        clean_line = keyword_line.strip().rstrip('+-% ').upper()

        # Both branches below describe why nothing matched, so they are only
        # true of a line that really did not resolve.  Checking here rather than
        # trusting the caller keeps the answer correct for either.
        if cls.resolve(clean_line) is not None:
            return None

        # A registered name that is a prefix of the line and was passed over:
        # only exact_match does that, so say which name and why.
        rejected = [name for name, klass in cls.KEYWORD_MAP.items()
                    if clean_line.startswith(name) and klass.exact_match]
        if rejected:
            closest = max(rejected, key=len)
            return (f"Unhandled keyword: {clean_line} -- {closest} is registered "
                    f"with exact_match, so the longer name is treated as a "
                    f"different keyword")

        # No registered name is a prefix, but one may share enough leading
        # tokens that the line looks like a sibling the registry misses.
        tokens = clean_line.lstrip('*').split('_')
        best = None
        best_shared = 0
        for name in cls.KEYWORD_MAP:
            shared = 0
            for token, other in zip(tokens, name.lstrip('*').split('_')):
                if token != other:
                    break
                shared += 1
            if shared > best_shared:
                best, best_shared = name, shared
        if best_shared >= cls.NEAR_MISS_TOKENS:
            return (f"Unhandled keyword: {clean_line} -- {best} is registered but "
                    f"is not a prefix of it; the registration may be too narrow")

        return None

    def has_option(self, option: str) -> bool:
        """Whether *option* is present in this keyword's option suffix.

        ``self.options`` is the option suffix split on ``'_'``, so a plain
        membership test cannot see a multi-token option: the options of
        ``*BOUNDARY_PRESCRIBED_MOTION_SET_BOX`` are ``['SET', 'BOX']``, and
        ``'SET_BOX' in kw.options`` is False.  This method matches *option*
        against a contiguous run of tokens instead, so ``SET_BOX`` is found
        while a token boundary is still respected --- ``has_option("ID")`` is
        False for ``*BOUNDARY_PRESCRIBED_MOTION_RIGID``.

        Note that one option name can be a prefix of another: for
        ``*ELEMENT_SHELL_COMPOSITE_LONG`` both ``has_option("COMPOSITE")`` and
        ``has_option("COMPOSITE_LONG")`` are True.  Callers that treat such
        options as alternatives must test the longer name first.

        Args:
            option: Option name, with underscores between tokens
                (``"SET_BOX"``, ``"ATTACHMENT_NODES"``).  Case-insensitive.

        Returns:
            True when the option is present.
        """
        option = option.strip('_').upper()
        if not option:
            return False
        suffix = '_' + '_'.join(o.upper() for o in self.options) + '_'
        return f"_{option}_" in suffix

    def _extract_title(self, raw_lines: List[str]) -> List[str]:
        """Take the title line off *raw_lines*, storing it in ``self.title``.

        For a keyword carrying the ``TITLE`` option the first line after the
        keyword line is a free-form title, not data.  Removing it here --- once,
        before any parsing --- is what lets every subclass support the option
        without knowing about it, including subclasses with their own
        ``_parse_raw_data``.

        Comment lines are skipped when looking for the title, exactly as the
        solver skips them.  A *blank* line is not skipped: LS-DYNA takes the
        first non-comment line as the title card whatever it holds, so a blank
        one is an empty title.  Skipping it instead would consume Card 1 as the
        title of a keyword that has none.

        Args:
            raw_lines: The whole block, ``raw_lines[0]`` being the keyword line.

        Returns:
            The block without the title line.  ``raw_lines`` unchanged when the
            keyword has no title.
        """
        if not self.supports_title or not self.has_option("TITLE"):
            return raw_lines
        for i, line in enumerate(raw_lines[1:], start=1):
            if line.lstrip().startswith('$'):
                continue
            self.title = line.rstrip()
            return raw_lines[:i] + raw_lines[i + 1:]
        return raw_lines

    def _write_keyword_line(self, file_obj: TextIO):
        """Write the keyword line, and the title line when there is one.

        Every ``write`` implementation should open with this rather than
        writing ``full_keyword`` itself, so that a title survives the round
        trip whether or not the class parses its cards itself.
        """
        file_obj.write(f"{self.full_keyword}\n")
        if self.title is not None:
            file_obj.write(f"{self.title}\n")

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data lines and populates self.cards.

        If ``card_groups`` is defined, uses interleaved grouped parsing.
        If ``card_schemas`` is defined, uses sequential schema parsing.
        Otherwise subclasses must override this method.
        """
        if self.card_groups:
            data_lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
            for group in self.card_groups:
                active = [s for s in group.schemas if not s.condition or s.condition(self)]
                self._parse_grouped_lines(data_lines, active)
            return
        if not self.card_schemas:
            raise NotImplementedError(
                f"{type(self).__name__} must define card_schemas/card_groups or override _parse_raw_data"
            )
        data_lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
        idx = 0
        for schema in self.card_schemas:
            if schema.condition and not schema.condition(self):
                continue
            if schema.repeating:
                self.cards[schema.name] = self._parse_repeating_card(data_lines[idx:], schema)
                break
            else:
                if idx < len(data_lines):
                    self.cards[schema.name] = self._parse_single_card(data_lines[idx], schema)
                    idx += 1

    def write(self, file_obj: TextIO):
        """
        Writes the keyword and its data to a file object.

        If ``card_groups`` is defined, uses interleaved grouped writing.
        If ``card_schemas`` is defined, uses sequential schema writing.
        Otherwise subclasses must override this method.
        """
        if self.card_groups:
            self._write_keyword_line(file_obj)
            for group in self.card_groups:
                active = [s for s in group.schemas if not s.condition or s.condition(self)]
                self._write_grouped_schemas(file_obj, active)
            return
        if not self.card_schemas:
            raise NotImplementedError(
                f"{type(self).__name__} must define card_schemas/card_groups or override write"
            )
        self._write_keyword_line(file_obj)
        for schema in self.card_schemas:
            if schema.condition and not schema.condition(self):
                continue
            card = self.cards.get(schema.name)
            if card is not None:
                self._write_card(file_obj, card, schema)

    # ------------------------------------------------------------------
    # Schema-driven helpers (used by the default _parse_raw_data / write)
    # ------------------------------------------------------------------

    _DTYPE_MAP = {'I': np.int32, 'F': np.float64, 'A': object}

    def _parse_single_card(self, line: str, schema: CardSchema) -> Dict[str, np.ndarray]:
        """Parse one fixed-width line into a dict of single-element numpy arrays."""
        values = self._parse_schema_line(line, schema)
        return {
            f.name: np.array(
                [values[i]],
                dtype=object if isinstance(values[i], ParameterRef) else self._DTYPE_MAP[f.type],
            )
            for i, f in enumerate(schema.fields) if f.stored
        }

    _BLANK = object()
    """Stands in for a blank field until its default is substituted."""

    def _parse_schema_line(self, line: str, schema: CardSchema) -> list:
        """Parse one line against *schema*: one value per field, in order.

        Blank fields read as 0, or as their declared ``default`` when the class
        sets :attr:`blank_means_default`.
        """
        field_types = [f.type for f in schema.fields]
        field_lens  = [f.width for f in schema.fields]
        if not self.blank_means_default:
            return self.parser.parse_line(line, field_types, field_len=field_lens)
        values = self.parser.parse_line(line, field_types, field_len=field_lens,
                                        default_value=self._BLANK)
        return [f.default if v is self._BLANK else v
                for v, f in zip(values, schema.fields)]

    def _parse_repeating_card(self, lines: List[str], schema: CardSchema) -> Dict[str, np.ndarray]:
        """Parse multiple fixed-width lines into a dict of numpy arrays (one row per line)."""
        col_dtypes  = [self._DTYPE_MAP[f.type] for f in schema.fields]

        parsed_data = []
        for line in lines:
            values = self._parse_schema_line(line, schema)
            if any(v is not None for v in values):
                parsed_data.append(values[:len(schema.fields)])

        stored = [(i, f) for i, f in enumerate(schema.fields) if f.stored]
        if parsed_data:
            arr = np.array(parsed_data, dtype=object)
            result = {}
            for i, f in stored:
                col_arr = arr[:, i]
                has_ref = any(isinstance(v, ParameterRef) for v in col_arr)
                result[f.name] = col_arr.astype(object if has_ref else col_dtypes[i], copy=False)
            return result
        else:
            return {f.name: np.array([], dtype=col_dtypes[i]) for i, f in stored}

    def _write_card(self, file_obj: TextIO, card: Dict[str, np.ndarray], schema: CardSchema):
        """Write one card (single or repeating) to file_obj."""
        if schema.write_header:
            file_obj.write(self.parser.format_header(
                [(f.header_name or f.name) if f.stored else ""
                 for f in schema.fields],
                field_len=[f.width for f in schema.fields],
            ))
        # A column declared with stored=False has no entry in the card and is
        # written blank, which keeps the columns after it in place.
        if schema.repeating:
            first = next(f.name for f in schema.fields if f.stored)
            n_rows = len(card[first])
            for idx in range(n_rows):
                parts = [
                    self.parser.format_field(
                        card[f.name][idx] if f.stored else None,
                        f.type, field_len=f.width)
                    for f in schema.fields
                ]
                file_obj.write(''.join(parts) + '\n')
        else:
            parts = [
                self.parser.format_field(
                    card[f.name][0] if f.stored else None,
                    f.type, field_len=f.width)
                for f in schema.fields
            ]
            file_obj.write(''.join(parts) + '\n')

    def _parse_grouped_lines(self, data_lines: List[str], schemas: List[CardSchema]):
        """Parse interleaved data lines into self.cards.

        Lines are assumed to cycle through schemas with a fixed stride equal to
        ``len(schemas)``:  line 0 → schema 0, line 1 → schema 1, ...,
        line N → schema 0 again, etc.
        """
        stride = len(schemas)
        if stride == 0:
            return
        for i, schema in enumerate(schemas):
            self.cards[schema.name] = self._parse_repeating_card(
                data_lines[i::stride], schema
            )

    def _write_grouped_schemas(self, file_obj: TextIO, schemas: List[CardSchema]):
        """Write headers once then interleaved data rows (one row per schema per element).

        For each schema, if a field name is absent from the card (e.g. trailing
        optional columns never parsed), it is written as blank space.
        """
        # 1. Headers
        for schema in schemas:
            if schema.write_header:
                file_obj.write(self.parser.format_header(
                    [f.header_name or f.name for f in schema.fields],
                    field_len=[f.width for f in schema.fields],
                ))

        if not schemas:
            return

        # Row count from the first schema's first field
        first_card = self.cards.get(schemas[0].name)
        if first_card is None:
            return
        n_rows = len(first_card[schemas[0].fields[0].name])

        # 2. Interleaved data rows
        for idx in range(n_rows):
            for schema in schemas:
                card = self.cards.get(schema.name)
                if card is None:
                    continue
                parts = [
                    self.parser.format_field(
                        card[f.name][idx] if f.name in card else None,
                        f.type,
                        field_len=f.width,
                    )
                    for f in schema.fields
                ]
                file_obj.write(''.join(parts) + '\n')

    def __repr__(self):
        return f"LSDynaKeyword(type={self.type.name}, options={self.options})"

    @staticmethod
    def discover_keywords():
        """
        Dynamically imports all keyword modules from the 'keywords' directory
        to ensure they are registered in the KEYWORD_MAP.
        """
        keyword_dir = os.path.dirname(__file__)
        for filename in os.listdir(keyword_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"dynakw.keywords.{filename[:-3]}"
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    # Handle potential import errors gracefully
                    print(f"Could not import {module_name}: {e}")
