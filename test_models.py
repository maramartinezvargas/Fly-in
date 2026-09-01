from src.models.zone import Zone
from src.models.connection import Connection
from src.models.graph import Graph


# Crear zonas
start = Zone("start", 0, 0)
middle = Zone("middle", 1, 0)
goal = Zone("goal", 2, 0)

# Crear grafo
graph = Graph()

graph.add_zone(start)
graph.add_zone(middle)
graph.add_zone(goal)

# Crear conexiones
connection1 = Connection(start, middle)
connection2 = Connection(middle, goal)

graph.add_connection(connection1)
graph.add_connection(connection2)


# Comprobar zonas
print("Zonas:")
print(graph.zones)

# Comprobar conexiones
print("\nConexiones:")
print(graph.connections)

# Comprobar conexiones de cada zona
print("\nConexiones de start:")
print(start.connections)

print("\nConexiones de middle:")
print(middle.connections)

print("\nConexiones de goal:")
print(goal.connections)

# Comprobar vecinos
print("\nVecinos de start:")
print([zone.name for zone in start.get_neighbors()])

print("\nVecinos de middle:")
print([zone.name for zone in middle.get_neighbors()])

print("\nVecinos de goal:")
print([zone.name for zone in goal.get_neighbors()])
