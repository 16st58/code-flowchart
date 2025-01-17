# code_flowchart/cli.py

import argparse
import sys
from .generator import CodeFlowchartGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate a flowchart from Python source code.")
    parser.add_argument("input_file", help="Path to the input Python file.")
    parser.add_argument("-o", "--output", default="code_flowchart", help="Output file name (without extension).")
    args = parser.parse_args()

    # Read code from an input file
    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    # generate flowchart
    generator = CodeFlowchartGenerator(code)
    generator.generate_flowchart(args.output)
