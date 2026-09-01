from src.parsing.parser import Parser


parser = Parser("maps/easy/01_linear_path.txt")
graph = parser.parse()

print("\nParser finished.")
print(f"Zones: {len(graph.zones)}")
print(f"Connections: {len(graph.connections)}")