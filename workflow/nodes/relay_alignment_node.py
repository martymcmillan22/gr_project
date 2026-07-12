try:
    from workflow.errors.strict_mode_errors import RelaySegmentError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.strict_mode_errors import RelaySegmentError


class RelayAlignmentNode:
    """
    Ensures the 4 colors form a contiguous segment of the Linear Relay.
    """

    def __init__(self, config):
        self.relay_order = config.get("relay_order", [])

    def run(self, inverse_pairs):
        """
        inverse_pairs: list of 2 tuples (color, inverse)
        returns: ordered 4-color relay segment
        """
        # Flatten pairs into a set of colors.
        colors = {c for pair in inverse_pairs for c in pair}

        # Find contiguous segment in relay_order.
        segment = []
        for i in range(len(self.relay_order) - 3):
            slice4 = self.relay_order[i : i + 4]
            if set(slice4) == colors:
                segment = slice4
                break

        if not segment:
            raise RelaySegmentError(sorted(colors))

        return segment
