from enum import Enum


class ZoneType(str, Enum):
    """Represent the different types of zones."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Represent a zone in the drone network."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
        is_start_or_end: bool = False,
    ) -> None:
        """Initialize a zone.

        Args:
            name: Unique name of the zone.
            x: X coordinate of the zone.
            y: Y coordinate of the zone.
            zone_type: Type of zone.
            color: Optional color used for visualization.
            max_drones: Maximum number of drones the zone can contain.
            is_start_or_end: Whether the zone is the start or end zone.
        """
        self.name = name

        # Position (Coordinates)
        self.x = x
        self.y = y

        # Characteristics
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

        # Status
        self.current_occupancy = 0
        self.is_start_or_end = is_start_or_end
