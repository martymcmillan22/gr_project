class InversePairNode:
    """
    Validates that the QPU contains two complete inverse color pairs.
    """

    def __init__(self, config):
        self.inverse_map = config.get("inverse_map", {})

    def run(self, colors):
        """
        colors: list of 4 color strings
        returns: list of 2 inverse pairs
        """
        pairs = []
        for color in colors:
            inverse = self.inverse_map.get(color)
            if inverse not in colors:
                raise ValueError(
                    f"Strict Mode Error: {color} appears without its inverse {inverse}."
                )
            pairs.append((color, inverse))

        # Deduplicate pairs (color <-> inverse)
        unique_pairs = []
        for a, b in pairs:
            if (b, a) not in unique_pairs:
                unique_pairs.append((a, b))

        if len(unique_pairs) != 2:
            raise ValueError("Strict Mode Error: QPU must contain exactly two inverse pairs.")

        return unique_pairs
