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

    def get_connection(self, zone_a: Zone, zone_b: Zone,) -> Connection | None:
        """Get the connection between two zones."""
        for connection in self.connections:
            if (
                connection.zone_a is zone_a
                and connection.zone_b is zone_b
            ) or (
                connection.zone_a is zone_b
                and connection.zone_b is zone_a
            ):
                return connection

        return None
