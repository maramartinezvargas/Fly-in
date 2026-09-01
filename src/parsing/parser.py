from src.models.graph import Graph


class Parser:
    """Parse a Fly-in map file."""

    def __init__(self, filename: str) -> None:
        """Initialize the parser.

        Args:
            filename: Path to the map file.
        """
        self.filename = filename

    def parse(self) -> Graph:
        """Parse the map file and return the graph.

        Returns:
            The graph described by the input file.
        """
        graph = Graph()

        with open(self.filename, "r") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                print(f"Line {line_number}: {line}")

        return graph
