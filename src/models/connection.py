from src.models.zone import Zone


class Connection:
    """Represent a bidirectional connection between two zones."""

    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        """Initialize a connection.

        Args:
            zone_a: The first zone of the connection.
            zone_b: The second zone of the connection.
            max_link_capacity: Maximum number of drones that can traverse
                the connection simultaneously.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        self.current_usage = 0
