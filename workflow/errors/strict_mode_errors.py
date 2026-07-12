class StrictModeError(Exception):
    """
    Base class for all Strict Mode workflow errors.
    Provides deterministic formatting and semantic tagging.
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ---------------------------------------------------------
# Inverse Pair Errors
# ---------------------------------------------------------


class InverseMissingError(StrictModeError):
    def __init__(self, color, inverse):
        super().__init__(
            code="STRICT_INVERSE_MISSING",
            message=f"Color '{color}' appears without its inverse '{inverse}'.",
        )


class InverseCountError(StrictModeError):
    def __init__(self):
        super().__init__(
            code="STRICT_INVERSE_COUNT",
            message="QPU must contain exactly two complete inverse pairs.",
        )


# ---------------------------------------------------------
# Relay Alignment Errors
# ---------------------------------------------------------


class RelaySegmentError(StrictModeError):
    def __init__(self, colors):
        super().__init__(
            code="STRICT_RELAY_SEGMENT",
            message=f"Colors {colors} do not form a contiguous Linear Relay segment.",
        )


# ---------------------------------------------------------
# SRL Errors
# ---------------------------------------------------------


class SRLGrowthError(StrictModeError):
    def __init__(self, expected_factor):
        super().__init__(
            code="STRICT_SRL_GROWTH",
            message=f"SRL values must follow x{expected_factor} growth across repositories.",
        )


# ---------------------------------------------------------
# Temporal Mapping Errors
# ---------------------------------------------------------


class TemporalCountError(StrictModeError):
    def __init__(self):
        super().__init__(
            code="STRICT_TEMPORAL_COUNT",
            message="Temporal mapping requires exactly 4 tenses.",
        )


class TemporalMappingError(StrictModeError):
    def __init__(self, tenses):
        super().__init__(
            code="STRICT_TEMPORAL_MAPPING",
            message=f"Invalid temporal mapping: {tenses}.",
        )
