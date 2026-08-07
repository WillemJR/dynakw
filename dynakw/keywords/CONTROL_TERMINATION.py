"""Implementation of the *CONTROL_TERMINATION keyword."""

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ControlTermination(LSDynaKeyword):
    """Implements the *CONTROL_TERMINATION keyword."""

    keyword_string = "*CONTROL_TERMINATION"

    description = (
        "Stops the job.  ENDTIM is mandatory; the remaining fields give "
        "earlier termination conditions on cycle count, time step, energy "
        "ratio and total mass."
    )
    manual_section = "Vol I, *CONTROL_TERMINATION"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("ENDTIM", "F", width=10,
                      description="Termination time; mandatory",
                      units="time", required=True),
            CardField("ENDCYC", "I", width=10,
                      description="Termination cycle, used if it is reached "
                                  "before the termination time"),
            CardField("DTMIN", "F", width=10,
                      description="Factor on the initial step size giving the "
                                  "minimum time step; reaching it terminates "
                                  "the run with a restart dump"),
            CardField("ENDENG", "F", width=10,
                      description="Percent change in energy ratio that "
                                  "terminates the run; inactive if undefined"),
            CardField("ENDMAS", "F", width=10, default=1.0e8,
                      description="Percent change in total mass that "
                                  "terminates the run; a negative value is a "
                                  "load curve ID.  Relevant only with mass "
                                  "scaling"),
            CardField("NOSOL", "I", width=10,
                      description="Non-solution run: terminate directly after "
                                  "initialization",
                      choices={0: "off (default)", 1: "on"}),
        ], write_header=True,
           description="Termination conditions."),
    ]
