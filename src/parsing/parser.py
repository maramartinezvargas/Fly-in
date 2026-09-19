from src.models.graph import Graph
from src.models.zone import Zone, ZoneType
from src.models.connection import Connection
from src.parsing.parser_error import ParserError


class Parser:
    """Parse a Fly-in map file."""

    def __init__(self, filename: str) -> None:
        """Initialize the parser.

        Args:
            filename: Path to the map file.
        """
        self.filename = filename
        self.nb_drones = 0
        self.nb_drones_defined = False
        self.start_zone: Zone | None = None
        self.end_zone: Zone | None = None
        self.connection_pairs: set[tuple[str, str]] = set()

    def parse(self) -> Graph:
        """Parse the map file and return the graph.

        Returns:
            The graph described by the input file.

        Raises:
            ParserError: If the map contains invalid syntax or data.
        """
        graph = Graph()

        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("nb_drones:"):
                        self._parse_nb_drones(line, line_number)
                    elif line.startswith(
                        ("start_hub:", "end_hub:", "hub:")
                    ):
                        self._parse_zone(graph, line, line_number)
                    elif line.startswith("connection:"):
                        self._parse_connection(graph, line, line_number)
                    else:
                        raise ParserError(
                            line_number,
                            "Unknown syntax",
                        )
        except FileNotFoundError:
            raise ParserError(0, f"Map file not found: {self.filename}")
        except OSError as error:
            raise ParserError(0, f"Could not read map file: {error}")

        self._validate_map()

        return graph

    def _parse_nb_drones(
        self,
        line: str,
        line_number: int,
    ) -> None:
        """Parse and validate the number of drones."""
        if self.nb_drones_defined:
            raise ParserError(
                line_number,
                "nb_drones can only be defined once",
            )

        value = line.split(":", 1)[1].strip()

        if not value:
            raise ParserError(
                line_number,
                "nb_drones must be a positive integer",
            )

        try:
            nb_drones = int(value)
        except ValueError:
            raise ParserError(
                line_number,
                "nb_drones must be a positive integer",
            )

        if nb_drones <= 0:
            raise ParserError(
                line_number,
                "nb_drones must be a positive integer",
            )

        self.nb_drones = nb_drones
        self.nb_drones_defined = True

    def _parse_zone(
        self,
        graph: Graph,
        line: str,
        line_number: int,
    ) -> None:
        """Parse and add a zone to the graph."""
        parts = line.split(":", 1)
        hub_type = parts[0]
        data = parts[1].strip()

        data_without_metadata = data.split("[", 1)[0].strip()
        values = data_without_metadata.split()

        if len(values) != 3:
            raise ParserError(
                line_number,
                "Zone must have a name and two integer coordinates",
            )

        name = values[0]

        if "-" in name:
            raise ParserError(
                line_number,
                "Zone names cannot contain dashes",
            )

        try:
            x = int(values[1])
            y = int(values[2])
        except ValueError:
            raise ParserError(
                line_number,
                "Zone coordinates must be integers",
            )

        if name in graph.zones:
            raise ParserError(
                line_number,
                f"Zone '{name}' is already defined",
            )

        metadata = self._parse_metadata(
            data,
            line_number,
            {"zone", "color", "max_drones"},
        )

        try:
            zone_type = ZoneType(
                metadata.get("zone", "normal")
            )
        except ValueError:
            raise ParserError(
                line_number,
                "Invalid zone type",
            )

        color = metadata.get("color")
        is_start_or_end = hub_type != "hub"

        if is_start_or_end:
            # max_drones is ignored for start_hub and end_hub.
            max_drones = 1
        else:
            max_drones = self._parse_positive_integer(
                metadata.get("max_drones", "1"),
                "max_drones must be a positive integer",
                line_number,
            )

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
            is_start_or_end=is_start_or_end,
        )

        graph.add_zone(zone)

        if hub_type == "start_hub":
            if self.start_zone is not None:
                raise ParserError(
                    line_number,
                    "Only one start_hub is allowed",
                )
            self.start_zone = zone

        elif hub_type == "end_hub":
            if self.end_zone is not None:
                raise ParserError(
                    line_number,
                    "Only one end_hub is allowed",
                )
            self.end_zone = zone

    def _parse_connection(
        self,
        graph: Graph,
        line: str,
        line_number: int,
    ) -> None:
        """Parse and add a connection to the graph."""
        data = line.split(":", 1)[1].strip()

        connection_without_metadata = data.split("[", 1)[0].strip()

        zone_names = connection_without_metadata.split("-")

        if len(zone_names) != 2:
            raise ParserError(
                line_number,
                "Connection must link two zones",
            )

        zone_a_name = zone_names[0].strip()
        zone_b_name = zone_names[1].strip()

        if not zone_a_name or not zone_b_name:
            raise ParserError(
                line_number,
                "Connection must link two zones",
            )

        if zone_a_name == zone_b_name:
            raise ParserError(
                line_number,
                "A connection cannot link a zone to itself",
            )

        if zone_a_name not in graph.zones:
            raise ParserError(
                line_number,
                f"Zone '{zone_a_name}' is not defined",
            )

        if zone_b_name not in graph.zones:
            raise ParserError(
                line_number,
                f"Zone '{zone_b_name}' is not defined",
            )

        pair = (
            min(zone_a_name, zone_b_name),
            max(zone_a_name, zone_b_name),
        )

        if pair in self.connection_pairs:
            raise ParserError(
                line_number,
                "Duplicate connection",
            )

        metadata = self._parse_metadata(
            data,
            line_number,
            {"max_link_capacity"},
        )

        max_link_capacity = self._parse_positive_integer(
            metadata.get("max_link_capacity", "1"),
            "max_link_capacity must be a positive integer",
            line_number,
        )

        zone_a = graph.zones[zone_a_name]
        zone_b = graph.zones[zone_b_name]

        connection = Connection(
            zone_a,
            zone_b,
            max_link_capacity,
        )

        graph.add_connection(connection)
        self.connection_pairs.add(pair)

    def _parse_metadata(
        self,
        data: str,
        line_number: int,
        allowed_keys: set[str],
    ) -> dict[str, str]:
        """Parse and validate metadata inside square brackets."""
        has_opening_bracket = "[" in data
        has_closing_bracket = "]" in data

        if has_opening_bracket != has_closing_bracket:
            raise ParserError(
                line_number,
                "Invalid metadata syntax",
            )

        if not has_opening_bracket:
            return {}

        if data.count("[") != 1 or data.count("]") != 1:
            raise ParserError(
                line_number,
                "Invalid metadata syntax",
            )

        metadata_text = data.split("[", 1)[1].split("]", 1)[0].strip()

        if not metadata_text:
            raise ParserError(
                line_number,
                "Metadata cannot be empty",
            )

        metadata: dict[str, str] = {}

        for item in metadata_text.split():
            if "=" not in item:
                raise ParserError(
                    line_number,
                    "Metadata must use key=value format",
                )

            key, value = item.split("=", 1)

            if not key or not value:
                raise ParserError(
                    line_number,
                    "Metadata must use key=value format",
                )

            if key not in allowed_keys:
                raise ParserError(
                    line_number,
                    f"Unknown metadata key '{key}'",
                )

            if key in metadata:
                raise ParserError(
                    line_number,
                    f"Metadata key '{key}' is duplicated",
                )

            metadata[key] = value

        return metadata

    def _parse_positive_integer(
        self,
        value: str,
        error_message: str,
        line_number: int,
    ) -> int:
        """Parse a positive integer."""
        try:
            number = int(value)
        except ValueError:
            raise ParserError(
                line_number,
                error_message,
            )

        if number <= 0:
            raise ParserError(
                line_number,
                error_message,
            )

        return number

    def _validate_map(self) -> None:
        """Validate required map elements after parsing."""
        if not self.nb_drones_defined:
            raise ParserError(
                0,
                "nb_drones is missing",
            )

        if self.start_zone is None:
            raise ParserError(
                0,
                "start_hub is missing",
            )

        if self.end_zone is None:
            raise ParserError(
                0,
                "end_hub is missing",
            )
