import ast
import json
from typing import Any


def get_test_data(filepath: str) -> Any:
    """
    Load and parse test data from a .txt or .json file.

    :param filepath: Path to the input file containing test data. Supports .txt files with Python literals
                     and .json files with JSON-formatted data.
    :return: Parsed Python object from the file contents.
    """
    if filepath.endswith(".txt"):
        with open(filepath, "r") as data:
            return ast.literal_eval(data.read())
    if filepath.endswith(".json"):
        with open(filepath, "r") as data:
            return json.load(data)
