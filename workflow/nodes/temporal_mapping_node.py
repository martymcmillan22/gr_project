try:
    from workflow.errors.strict_mode_errors import TemporalCountError, TemporalMappingError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.strict_mode_errors import TemporalCountError, TemporalMappingError


class TemporalMappingNode:
    """
    Maps the 4 colors to Past -> Present-Past -> Present-Future -> Future.
    """

    def __init__(self, config):
        self.tenses = config.get("tenses", [])

    def run(self, srl_values):
        """
        srl_values: list of 4 SRL values
        returns: final QPU structure
        """
        if len(self.tenses) != 4:
            raise TemporalCountError()

        qpu = []
        for tense, srl in zip(self.tenses, srl_values):
            if not tense:
                raise TemporalMappingError(self.tenses)
            qpu.append({"tense": tense, "srl": srl})

        return qpu
