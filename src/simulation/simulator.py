from src.models.connection import Connection
from src.models.drone import Drone, DroneStatus
from src.models.graph import Graph
from src.models.zone import Zone, ZoneType
from src.pathfinding.pathfinder import Pathfinder


class Simulator:
    """Simulate drones moving through the map."""

    def __init__(
        self,
        graph: Graph,
        nb_drones: int,
        start_zone: Zone,
        end_zone: Zone,
    ) -> None:
        """Initialize the simulation.

        Args:
            graph: Graph containing the map.
            nb_drones: Number of drones to simulate.
            start_zone: Starting zone.
            end_zone: Destination zone.
        """
        self.graph = graph
        self.nb_drones = nb_drones
        self.start_zone = start_zone
        self.end_zone = end_zone

        self.pathfinder = Pathfinder(graph)
        self.drones: list[Drone] = []
        self.turn = 0
        self.output: list[str] = []

        self._create_drones()
        self._assign_paths()

    def _create_drones(self) -> None:
        """Create all drones at the starting zone."""
        for number in range(1, self.nb_drones + 1):
            drone = Drone(
                drone_id=f"D{number}",
                starting_zone=self.start_zone,
            )
            drone.destination_zone = self.end_zone
            self.drones.append(drone)

    def _assign_paths(self) -> None:
        """Assign initial candidate paths to all drones."""
        paths = self.pathfinder.find_paths(
            self.start_zone,
            self.end_zone,
        )

        for drone in self.drones:
            drone.candidate_paths = [
                path.copy() for path in paths
            ]
            drone.path = paths[0].copy()
            drone.current_step = 0

    def run(self) -> list[str]:
        """Run the simulation until all drones are delivered.

        Returns:
            The movement output for every turn.
        """
        while not self._all_drones_delivered():
            self.turn += 1
            movements = self._process_turn()

            if movements:
                self.output.append(
                    f"Turn {self.turn}: "
                    + " ".join(movements)
                )

        return self.output

    def _process_turn(self) -> list[str]:
        """Process all drone movements for the current turn."""
        movements: list[str] = []
        completed_transit: set[Drone] = set()

        for drone in self.drones:
            if drone.status == DroneStatus.DELIVERED:
                continue

            if drone.status == DroneStatus.IN_TRANSIT:
                movement = self._process_transit(drone)

                if movement is not None:
                    movements.append(movement)

                if drone.status != DroneStatus.IN_TRANSIT:
                    completed_transit.add(drone)

                continue

        requested_moves: dict[Drone, Zone] = {}

        for drone in self.drones:
            if drone.status == DroneStatus.DELIVERED:
                continue

            if drone.status == DroneStatus.IN_TRANSIT:
                continue

            if drone in completed_transit:
                continue

            next_zone = self._get_next_zone(drone)

            if next_zone is not None:
                requested_moves[drone] = next_zone

        approved_moves = self._approve_moves(requested_moves)

        for drone, next_zone in approved_moves.items():
            movement = self._apply_move(drone, next_zone)

            if movement is not None:
                movements.append(movement)

        return movements

    def _process_transit(
        self,
        drone: Drone,
    ) -> str | None:
        """Advance a drone currently in a restricted movement."""
        if drone.current_connection is None:
            raise ValueError(
                f"Drone '{drone.id}' is in transit without a connection"
            )

        drone.remaining_turns -= 1

        if drone.remaining_turns > 0:
            return f"{drone.id}-connection"

        return self._finish_transit(drone)

    def _finish_transit(
        self,
        drone: Drone,
    ) -> str:
        """Finish a restricted movement."""
        connection = drone.current_connection

        if connection is None:
            raise ValueError(
                f"Drone '{drone.id}' is in transit without a connection"
            )

        destination = drone.path[drone.current_step + 1]

        connection.current_usage -= 1
        drone.current_connection = None

        self._enter_zone(destination)

        drone.current_zone = destination
        drone.current_step += 1
        drone.remaining_turns = 0
        drone.status = DroneStatus.MOVING

        if destination is self.end_zone:
            drone.status = DroneStatus.DELIVERED

        return f"{drone.id}-{destination.name}"

    def _get_next_zone(self, drone: Drone) -> Zone | None:
        """Return the next zone requested by a drone."""
        if drone.current_zone is None:
            return None

        if drone.current_step >= len(drone.path) - 1:
            drone.status = DroneStatus.DELIVERED
            return None

        return drone.path[drone.current_step + 1]

    def _approve_moves(
        self,
        requested_moves: dict[Drone, Zone],
    ) -> dict[Drone, Zone]:
        """Approve compatible movements for the current turn."""
        approved_moves: dict[Drone, Zone] = {}
        reserved_zone_capacity: dict[Zone, int] = {}
        reserved_link_capacity: dict[Connection, int] = {}

        for drone, next_zone in requested_moves.items():
            current_zone = drone.current_zone

            if current_zone is None:
                continue

            connection = self._get_connection(
                current_zone,
                next_zone,
            )

            if next_zone.is_start_or_end:
                zone_available = True
            else:
                current_occupancy = next_zone.current_occupancy

                leaving = 0
                for (
                    other_drone,
                    other_next_zone,
                ) in requested_moves.items():
                    if other_drone.current_zone is next_zone:
                        leaving += 1

                zone_available = (
                    next_zone.max_drones
                    - current_occupancy
                    + leaving
                    - reserved_zone_capacity.get(next_zone, 0)
                    > 0
                )

            link_available = (
                connection.max_link_capacity
                - connection.current_usage
                - reserved_link_capacity.get(connection, 0)
                > 0
            )

            if zone_available and link_available:
                approved_moves[drone] = next_zone

                if not next_zone.is_start_or_end:
                    reserved_zone_capacity[next_zone] = (
                        reserved_zone_capacity.get(next_zone, 0) + 1
                    )

                reserved_link_capacity[connection] = (
                    reserved_link_capacity.get(connection, 0) + 1
                )
            else:
                alternative_path = self._find_alternative_path(drone)

                if alternative_path is not None:
                    self._switch_to_path(drone, alternative_path)

                drone.status = DroneStatus.WAITING

        return approved_moves

    def _can_enter_zone(
        self,
        zone: Zone,
        requested_count: int,
    ) -> bool:
        """Check whether a zone can accept a requested movement."""
        if zone.is_start_or_end:
            return True

        available_capacity = (
            zone.max_drones - zone.current_occupancy
        )

        return requested_count <= available_capacity

    def _apply_move(
        self,
        drone: Drone,
        next_zone: Zone,
    ) -> str | None:
        """Apply an approved movement."""
        current_zone = drone.current_zone

        if current_zone is None:
            return None

        connection = self._get_connection(
            current_zone,
            next_zone,
        )

        if next_zone.zone_type == ZoneType.RESTRICTED:
            connection.current_usage += 1

            drone.current_connection = connection
            drone.remaining_turns = 2
            drone.status = DroneStatus.IN_TRANSIT

            return f"{drone.id}-connection"

        self._leave_zone(current_zone)
        self._enter_zone(next_zone)

        connection.current_usage += 1

        drone.current_zone = next_zone
        drone.current_step += 1
        drone.status = DroneStatus.MOVING

        connection.current_usage -= 1

        if next_zone is self.end_zone:
            drone.status = DroneStatus.DELIVERED

        return f"{drone.id}-{next_zone.name}"

    def _enter_zone(self, zone: Zone) -> None:
        """Increase the occupancy of a zone."""
        if not zone.is_start_or_end:
            zone.current_occupancy += 1

    def _leave_zone(self, zone: Zone) -> None:
        """Decrease the occupancy of a zone."""
        if not zone.is_start_or_end and zone.current_occupancy > 0:
            zone.current_occupancy -= 1

    def _all_drones_delivered(self) -> bool:
        """Return whether every drone reached the destination."""
        return all(
            drone.status == DroneStatus.DELIVERED
            for drone in self.drones
        )

    def _get_connection(
        self,
        current_zone: Zone,
        next_zone: Zone,
    ) -> Connection:
        """Get the connection used to move between two zones."""
        connection = self.graph.get_connection(current_zone, next_zone)

        if connection is None:
            raise ValueError(
                f"No connection found between "
                f"'{current_zone.name}' and '{next_zone.name}'"
            )

        return connection

    def _switch_to_path(
        self,
        drone: Drone,
        new_path: list[Zone],
    ) -> bool:
        """Switch a drone to a candidate path at its current zone."""
        current_zone = drone.current_zone

        if current_zone is None:
            return False

        try:
            new_step = new_path.index(current_zone)
        except ValueError:
            return False

        drone.path = new_path.copy()
        drone.current_step = new_step

        return True

    def _find_alternative_path(
        self,
        drone: Drone,
    ) -> list[Zone] | None:
        """Find a candidate path with a different next zone."""
        current_zone = drone.current_zone

        if current_zone is None:
            return None

        current_path = drone.path
        current_step = drone.current_step

        if current_step >= len(current_path) - 1:
            return None

        current_next_zone = current_path[current_step + 1]

        for candidate_path in drone.candidate_paths:
            if candidate_path == current_path:
                continue

            if current_zone not in candidate_path:
                continue

            candidate_step = candidate_path.index(current_zone)

            if candidate_step >= len(candidate_path) - 1:
                continue

            candidate_next_zone = candidate_path[candidate_step + 1]

            if candidate_next_zone is current_next_zone:
                continue

            return candidate_path

        return None
