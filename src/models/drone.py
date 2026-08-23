from enum import StrEnum

from src.models.connection import Connection
from src.models.zone import Zone


class DroneStatus(StrEnum):
    """Represent the possible states of a drone."""

    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class Drone:
    """Represent a drone moving through the network."""

    def __init__(
        self,
        drone_id: str,
        starting_zone: Zone,
    ) -> None:
        """Initialize a drone.

        Args:
            drone_id: Unique identifier of the drone.
            starting_zone: Zone where the drone starts.
        """
        self.id = drone_id
        self.current_zone: Zone | None = starting_zone
        self.current_connection: Connection | None = None
        self.status = DroneStatus.WAITING
        self.path: list[Zone] = []
        self.current_step = 0
        self.remaining_turns = 0
        self.destination_zone: Zone | None = None
