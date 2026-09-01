from src.models.connection import Connection
from src.models.zone import Zone


class Graph:
    """Represent the network of zones and connections."""

    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph.

        Args:
            zone: Zone to add.
        """
        self.zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        """Add a bidirectional connection to the graph.

        Args:
            connection: Connection to add.
        """
        self.connections.append(connection)
        connection.zone_a.connections.append(connection)
        connection.zone_b.connections.append(connection)