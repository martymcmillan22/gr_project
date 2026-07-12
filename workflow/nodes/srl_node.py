try:
    from workflow.errors.strict_mode_errors import SRLGrowthError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.strict_mode_errors import SRLGrowthError


class SRLNode:
    """
    Validates SRL compartments follow x4 growth across the 4 repositories.
    """

    def __init__(self, config):
        self.growth_factor = config.get("growth_factor", 4)

    def run(self, relay_segment):
        """
        relay_segment: ordered list of 4 colors
        returns: list of 4 SRL values
        """
        if self.growth_factor <= 1:
            raise SRLGrowthError(self.growth_factor)
        if len(relay_segment) != 4:
            raise SRLGrowthError(self.growth_factor)

        # Generate SRL values based on growth factor.
        srl_values = [4]
        for _ in range(3):
            srl_values.append(srl_values[-1] * self.growth_factor)

        return srl_values
