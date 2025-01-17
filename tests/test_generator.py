import os
import pytest
from code_flowchart.generator import CodeFlowchartGenerator

def test_generate_flowchart(tmp_path):
    sample_code = """
def greet(name):
    if name:
        print(f"Hello, {name}!")
    else:
        print("Hello, world!")
    return "Greeting complete"

greet("Alice")
"""
    output_file = tmp_path / "test_flowchart"
    generator = CodeFlowchartGenerator(sample_code)
    generator.generate_flowchart(str(output_file))

    # DOT 파일과 PNG 파일이 생성되었는지 확인
    dot_path = output_file.with_suffix(".dot")
    png_path = output_file.with_suffix(".png")

    assert dot_path.exists(), "DOT file was not generated."
    assert png_path.exists(), "PNG file was not generated."
