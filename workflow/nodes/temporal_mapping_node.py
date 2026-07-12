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
            raise ValueError("Strict Mode Error: Temporal mapping requires exactly 4 tenses.")

        qpu = []
        for tense, srl in zip(self.tenses, srl_values):
            qpu.append({"tense": tense, "srl": srl})

        return qpu
