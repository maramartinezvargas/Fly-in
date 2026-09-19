from src.models.graph import Graph
from src.models.zone import Zone, ZoneType


class Pathfinder:
    """Find paths through the Fly-in map."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the pathfinder.

        Args:
            graph: Graph containing the map zones and connections.
        """
        self.graph = graph

    def find_path(
        self,
        start: Zone,
        end: Zone,
    ) -> list[Zone]:
        """Find the lowest-cost path between two zones.

        Args:
            start: Starting zone.
            end: Destination zone.

        Returns:
            A list of zones representing the path.

        Raises:
            ValueError: If no path exists.
        """
        distances: dict[Zone, int] = {
            # Use a large number to represent infinity (for mypy compatibility)
            zone: 10**9 for zone in self.graph.zones.values()
        }
        previous: dict[Zone, Zone | None] = {
            zone: None for zone in self.graph.zones.values()
        }

        distances[start] = 0
        unvisited = set(self.graph.zones.values())

        while unvisited:
            current = min(
                unvisited,
                key=lambda zone: distances[zone],
            )

            if distances[current] == float("inf"):
                break

            unvisited.remove(current)

            if current is end:
                break

            if current.zone_type == ZoneType.BLOCKED:
                continue

            for neighbor in current.get_neighbors():
                if neighbor not in unvisited:
                    continue

                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                new_distance = (
                    distances[current]
                    + self._get_zone_cost(neighbor)
                )

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

        if distances[end] == float("inf"):
            raise ValueError(
                f"No path found from '{start.name}' "
                f"to '{end.name}'"
            )

        return self._build_path(previous, start, end)

    def _get_zone_cost(self, zone: Zone) -> int:
        """Return the traversal cost of a zone."""
        if zone.zone_type == ZoneType.RESTRICTED:
            return 2

        return 1

    def _build_path(
        self,
        previous: dict[Zone, Zone | None],
        start: Zone,
        end: Zone,
    ) -> list[Zone]:
        """Build the path from the predecessor map."""
        path: list[Zone] = []
        current: Zone | None = end

        while current is not None:
            path.append(current)

            if current is start:
                break

            current = previous[current]

        path.reverse()

        return path
