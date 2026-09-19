from src.parsing.parser import Parser
from src.parsing.parser_error import ParserError


def main() -> None:
    try:
        parser = Parser("maps/easy/01_linear_path.txt")
        parser.parse()
        print("Map parsed successfully.")
    except ParserError as error:
        print(error)


if __name__ == "__main__":
    main()
