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

            if distances[current] == 10**9:
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

        if distances[end] == 10**9:
            raise ValueError(
                f"No path found from '{start.name}' "
                f"to '{end.name}'"
            )

        return self._build_path(previous, start, end)

    def find_paths(
        self,
        start: Zone,
        end: Zone,
        max_paths: int = 3,
    ) -> list[list[Zone]]:
        """Find the lowest-cost alternative paths.

        Args:
            start: Starting zone.
            end: Destination zone.
            max_paths: Maximum number of paths to return.

        Returns:
            A list of paths ordered by cost.

        Raises:
            ValueError: If max_paths is not positive or no path exists.
        """
        if max_paths <= 0:
            raise ValueError("max_paths must be positive")

        all_paths: list[list[Zone]] = []

        self._search_paths(
            current=start,
            end=end,
            current_path=[start],
            paths=all_paths,
        )

        if not all_paths:
            raise ValueError(
                f"No path found from '{start.name}' "
                f"to '{end.name}'"
            )

        all_paths.sort(
            key=lambda path: (
                self._path_cost(path),
                len(path),
            )
        )

        return all_paths[:max_paths]

    def _search_paths(
        self,
        current: Zone,
        end: Zone,
        current_path: list[Zone],
        paths: list[list[Zone]],
    ) -> None:
        """Search for all simple paths between two zones."""
        if current is end:
            paths.append(current_path.copy())
            return

        for neighbor in current.get_neighbors():
            if neighbor in current_path:
                continue

            if neighbor.zone_type == ZoneType.BLOCKED:
                continue

            current_path.append(neighbor)

            self._search_paths(
                current=neighbor,
                end=end,
                current_path=current_path,
                paths=paths,
            )

            current_path.pop()

    def _path_cost(self, path: list[Zone]) -> int:
        """Calculate the total cost of a path."""
        return sum(
            self._get_zone_cost(zone)
            for zone in path[1:]
        )

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
