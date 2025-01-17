<h1 align="center">code-flowchart</h1>

![GitHub Tag](https://img.shields.io/github/v/tag/16st58/code-flowchart)
![PyPI - Version](https://img.shields.io/pypi/v/code-flowchart)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/code_flowchart)
![GitHub License](https://img.shields.io/github/license/16st58/code_flowchart)

**code-flowchart** is a simple tool for generating flowcharts (in both DOT and PNG formats) directly from your Python source code. It leverages Python's built-in AST (Abstract Syntax Tree) parsing and utilizes Graphviz to render visual diagrams.


## Installation
Install via pip:
```shell
pip install code-flowchart
```
**Note**  
This tool depends on [Graphviz](https://graphviz.org/). Even if you install a Python package for Graphviz, you might need to install Graphviz system-wide or configure your environment path. If you encounter issues, try installing Graphviz via conda:
```shell
conda install graphviz
```

## Usage
Once installed, you can run **code-flowchart** from the command line:
```shell
code_flowchart {python_file_path} -o {output_file_name}
```
* `{python_file_path}`: Path to your Python source file.
* `-o {output_file_name}`: (Optional) Output filename prefix.
By default, it saves as `code_flowchart.dot` and `code_flowchart.png`.

The command will generate a **DOT** file (`.dot`) and a corresponding **PNG** image in the current directory.

## Example
Consider the following **main.py**
```python
def isOdd(num):
    if not num%2==0:
        return True
    else:
        print("It's not odd!!!")
    return False

for i in range(3):
    print(isOdd(i))
```
To create a flowchart (DOT + PNG), simply run:
```shell
code_flowchart main.py -o output
```
<br>

**output.dot**
<details>
<summary>Click to expand</summary>

```dot
digraph {
	rankdir=TB
	nodesep=0.5 ranksep=0.75
	dpi=300 size="10,10"
{rank=source; "start_1";}{rank=same; "for_2";}{rank=same; "expr_3";}{rank=same; "call_4";}{rank=same; "function_5";}{rank=same; "if_6";}{rank=same; "return_7";}{rank=same; "else_8";}{rank=same; "return_9";}{rank=same; "if_end_10";}	return_7 -> call_4 [label=Return color=black fontsize=10 style=dashed]
	return_9 -> call_4 [label=Return color=black fontsize=10 style=dashed]
{rank=sink; "end_11";}	subgraph cluster_functions {
		color=green fontsize=16 label=Functions style=dashed
		function_5 [label="Function: isOdd" fontsize=12 shape=ellipse]
		if_6 [label="If: num % 2 == 0" fontsize=12 shape=diamond]
		function_5 -> if_6 [label="" color=black fontsize=10 style=solid]
		return_7 [label="Return: \"It's not odd!!!\"" fontsize=12 shape=box]
		if_6 -> return_7 [label=True color=black fontsize=10 style=solid]
		else_8 [label=Else fontsize=12 shape=diamond]
		if_6 -> else_8 [label=False color=black fontsize=10 style=solid]
		return_9 [label="Return: \"It's odd!!!\"" fontsize=12 shape=box]
		else_8 -> return_9 [label="" color=black fontsize=10 style=solid]
		if_end_10 [label="If End" fontsize=12 shape=circle]
	}
	subgraph cluster_main {
		color=blue fontsize=16 label="Main Code" style=dashed
		start_1 [label=Start fontsize=12 shape=ellipse]
		for_2 [label="For: i in range(3)" fontsize=12 shape=box]
		start_1 -> for_2 [label="" color=black fontsize=10 style=solid]
		expr_3 [label="Expression: print(isOdd(i))" fontsize=12 shape=box]
		for_2 -> expr_3 [label="" color=black fontsize=10 style=solid]
		call_4 [label="Call: isOdd(i)" fontsize=12 shape=box]
		expr_3 -> call_4 [label="Arg Call" color=black fontsize=10 style=solid]
		call_4 -> function_5 [label=Call color=black fontsize=10 style=dashed]
		expr_3 -> for_2 [label=Repeat color=black fontsize=10 style=dotted]
		end_11 [label=End fontsize=12 shape=ellipse]
		for_2 -> end_11 [label="" color=black fontsize=10 style=solid]
	}
}
```
</details>
<br>

**output.png**

Below is a preview of the generated flowchart (the actual image may vary based on the code and your Graphviz configuration):

<img src="output.png" width="200"/>

## Supported syntax
The library currently supports visualizing:
* **FunctionDef** (function definitions)
* **Call** (function calls, including user-defined functions)
* **If / Else / Elif**
* **For**
* **While**
* **Return**
* **Expr** (print, assignments, or any standalone expressions)
Other Python syntax nodes are either skipped or handled as generic expressions.

## License
This project is licensed under the MIT License.  
Feel free to use, modify, and distribute this tool in accordance with the license terms.  
Contributions are welcome!
