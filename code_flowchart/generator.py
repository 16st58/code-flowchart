import ast
from graphviz import Digraph

class CodeFlowchartGenerator:
    """
    A class that automatically generates flowcharts
    by parsing the given Python source code (AST).
    Creates PNG images and DOT files using Graphviz.
    """

    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)
        self.graph = Digraph(format='png')
        self.graph.attr(rankdir="TB")  # Top-to-Bottom layout
        self.graph.attr(nodesep="0.5", ranksep="0.75")  # Spacing between nodes and ranks
        self.graph.attr(size="10,10", dpi="300")  # Output image size & resolution
        self.counter = 0  # Node ID counter
        self.function_definitions = {}
        self.function_flow_nodes = {}
        self.node_prefix_map = {}  # Manage prefix for each node ID

        # Subgraph to contain the main flow
        self.main_cluster = Digraph(name="cluster_main")
        self.main_cluster.attr(label="Main Code", fontsize="16", style="dashed", color="blue")

        # Subgraph to contain function definitions
        self.function_cluster = Digraph(name="cluster_functions")
        self.function_cluster.attr(label="Functions", fontsize="16", style="dashed", color="green")

        # Pre-collect function definitions
        self._gather_function_definitions(self.tree)

    def _get_unique_id(self, prefix="node"):
        """Generates a unique node ID with the given prefix."""
        self.counter += 1
        node_id = f"{prefix}_{self.counter}"
        self.node_prefix_map[node_id] = prefix
        return node_id

    def _add_node(self, label, shape="box", cluster=None, prefix="node", rank="same"):
        """Adds a node to the graph (or subgraph) and returns the node ID."""
        node_id = self._get_unique_id(prefix)
        if cluster:
            cluster.node(node_id, label, shape=shape, fontsize="12")
        else:
            self.graph.node(node_id, label, shape=shape, fontsize="12")

        # Set rank
        if rank:
            self.graph.body.append(f'{{rank={rank}; "{node_id}";}}')

        return node_id

    def _add_edge(self, from_node, to_node, label="", cluster=None, color="black", style="solid"):
        """Adds an edge to the graph (or subgraph)."""
        if cluster:
            cluster.edge(from_node, to_node, label=label, fontsize="10", color=color, style=style)
        else:
            self.graph.edge(from_node, to_node, label=label, fontsize="10", color=color, style=style)

    def _get_node_prefix(self, node_id):
        """Returns the prefix corresponding to the node ID."""
        return self.node_prefix_map.get(node_id, "unknown")

    def _gather_function_definitions(self, node: ast.AST):
        """Traverses the entire AST and pre-collects only function definitions (ast.FunctionDef)."""
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef):
                self.function_definitions[child.name] = child

    def _is_major_statement(self, stmt: ast.stmt):
        """
        Determines whether the statement is a 'major statement':
        - if, for, while, function def, return
        - Checks for user-defined function calls (including nested ones).
        """
        # 1) if / for / while / function def / return are immediately True
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.FunctionDef, ast.Return)):
            return True

        # 2) Traverse all child nodes of stmt to find ast.Call
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                # Extract the name of the function being called
                try:
                    func_name = ast.unparse(node.func)
                except Exception:
                    func_name = None

                # Check if the name is in the list of user-defined functions
                if func_name and func_name in self.function_definitions:
                    return True

        # 3) If it doesn't meet any of the above conditions, return False
        return False

    def _grouped_statements(self, stmts):
        """
        Iterates through a list of statements, processes major statements individually,
        and groups consecutive minor statements into one group (list).

        Example:
        [Expr(1), Expr(2), If(...), Expr(3), Expr(4), While(...)]
        -> [[Expr(1), Expr(2)], If(...), [Expr(3), Expr(4)], While(...)]
        """
        grouped = []
        buffer = []

        for stmt in stmts:
            if self._is_major_statement(stmt):
                if buffer:
                    grouped.append(buffer)
                    buffer = []
                grouped.append(stmt)
            else:
                buffer.append(stmt)

        if buffer:
            grouped.append(buffer)

        return grouped

    def _process_body(self, stmts, cluster, start_node, return_points=None):
        """
        Processes multiple statements (or statement groups) sequentially
        and returns the last node.
        """
        if return_points is None:
            return_points = []

        current_node = start_node
        grouped = self._grouped_statements(stmts)

        for group in grouped:
            current_node = self._process_node(group, current_node, cluster=cluster, return_points=return_points)

        return current_node
    
    def _process_function_call(self, call_node, current_node, cluster, edge_label=""):
        """
        Processes a function call at the current code position.
        If there are nested function calls among the arguments, processes them recursively.
        """
        func_name = ast.unparse(call_node.func)
        expr_content = ast.unparse(call_node)

        # 1) User-defined function?
        if func_name in self.function_definitions:
            # Create a Call node
            expr_node = self._add_node(f"Call: {expr_content}", "box", cluster=cluster, prefix="call")
            self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)

            # Generate nodes for the function's internal flow in the function cluster
            func_def = self.function_definitions[func_name]
            if func_name not in self.function_flow_nodes:
                # If no nodes exist for the function, create them
                func_start_node = self._add_node(
                    f"Function: {func_name}", "ellipse",
                    cluster=self.function_cluster, prefix="function"
                )
                func_return_points = []
                func_body_node = self._process_body(
                    func_def.body, self.function_cluster,
                    func_start_node, func_return_points
                )
                func_end_node = func_body_node
                self.function_flow_nodes[func_name] = (func_start_node, func_end_node, func_return_points)
            else:
                func_start_node = self.function_flow_nodes[func_name][0]

            # Connect the function call node to the function start node in the main cluster with a dashed line
            self._add_edge(expr_node, func_start_node, label="Call", cluster=self.main_cluster, style="dashed")

            # Link function return points back to the function call node
            for return_node in self.function_flow_nodes[func_name][2]:
                self._add_edge(return_node, expr_node, label="Return", style="dashed")

            # 2) Check for nested function calls among arguments
            for arg in call_node.args:
                if isinstance(arg, ast.Call):
                    # Process recursively
                    self._process_function_call(arg, expr_node, cluster, edge_label="Arg Call")

            return expr_node

        else:
            # External or library function
            expr_node = self._add_node(f"Expression: {expr_content}", "box", cluster=cluster, prefix="expr")
            self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)

            # Check for nested function calls in arguments
            for arg in call_node.args:
                if isinstance(arg, ast.Call):
                    # Process recursively
                    self._process_function_call(arg, expr_node, cluster, edge_label="Arg Call")

            # Process keyword arguments
            for kw in call_node.keywords:
                if isinstance(kw.value, ast.Call):
                    self._process_function_call(kw.value, expr_node, cluster, edge_label="Arg Call")

            return expr_node

    def _process_node(self, node, current_node, cluster=None, return_points=None, edge_label=""):
        """
        Processes an AST node (or list of nodes) and generates corresponding
        flowchart nodes, connects them, and returns the next node.
        """
        if return_points is None:
            return_points = []

        # 1) List of multiple minor statements
        if isinstance(node, list):
            expr_node = self._add_node("Expression", "box", cluster=cluster, prefix="expr")
            self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)
            return expr_node

        # 2) FunctionDef (function definition)
        elif isinstance(node, ast.FunctionDef):
            # Function definition nodes are bypassed in the main code flow
            return current_node

        # 3) Expression (function call/simple expressions, etc.)
        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                return self._process_function_call(node.value, current_node, cluster)
            else:
                # Simple expression
                expr_content = ast.unparse(node.value)
                expr_node = self._add_node(f"Expression: {expr_content}", "box", cluster=cluster, prefix="expr")
                self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)
                return expr_node

        # 4) If statement
        elif isinstance(node, ast.If):
            condition = ast.unparse(node.test)
            if_node = self._add_node(f"If: {condition}", "diamond", cluster=cluster, prefix="if")
            self._add_edge(current_node, if_node, cluster=cluster)

            body_node = if_node
            if_end_node = body_node
            is_first_true_edge = True

            # If body
            grouped_body = self._grouped_statements(node.body)
            for g in grouped_body:
                edge_label_for_body = "True" if is_first_true_edge else ""
                if_end_node = self._process_node(g, if_end_node, cluster=cluster, return_points=return_points,
                                                 edge_label=edge_label_for_body)
                is_first_true_edge = False

            end_nodes = [if_end_node]

            # Else/Elif handling
            if node.orelse:
                first_else_node = node.orelse[0] if node.orelse else None
                if isinstance(first_else_node, ast.If):
                    # If it's an elif
                    elif_end_node = self._process_node(
                        first_else_node, if_node, cluster=cluster, return_points=return_points, edge_label="False"
                    )
                    # Remaining else of the first elif is processed as first_else_node.orelse
                    node.orelse = first_else_node.orelse
                    end_nodes.append(elif_end_node)
                else:
                    else_node = self._add_node("Else", "diamond", cluster=cluster, prefix="else")
                    self._add_edge(if_node, else_node, "False", cluster=cluster)
                    else_end_node = else_node
                    grouped_orelse = self._grouped_statements(node.orelse)
                    for g in grouped_orelse:
                        else_end_node = self._process_node(g, else_end_node, cluster=cluster, return_points=return_points)
                    end_nodes.append(else_end_node)

            # Merge point at the end of If
            merge_node = self._add_node("If End", "circle", cluster=cluster, prefix="if_end")
            for end_node in end_nodes:
                if self._get_node_prefix(end_node) != "return":  # Do not connect return nodes to merge
                    self._add_edge(end_node, merge_node, cluster=cluster)

            return merge_node

        # 5) For loop
        elif isinstance(node, ast.For):
            target = ast.unparse(node.target)
            iter_ = ast.unparse(node.iter)
            for_node = self._add_node(f"For: {target} in {iter_}", "parallelogram", cluster=cluster, prefix="for")
            self._add_edge(current_node, for_node, cluster=cluster)

            # For loop body
            body_node = for_node
            body_node = self._process_body(node.body, cluster, body_node, return_points)

            # Loop back to the start of the for node
            self._add_edge(body_node, for_node, "Repeat", cluster=cluster, style="dotted")
            return for_node

        # 6) While loop
        elif isinstance(node, ast.While):
            condition = ast.unparse(node.test)
            while_node = self._add_node(f"While: {condition}", "parallelogram", cluster=cluster, prefix="while")
            self._add_edge(current_node, while_node, cluster=cluster)

            # While loop body
            body_node = while_node
            body_node = self._process_body(node.body, cluster, body_node, return_points)

            # Loop back to the start of the while node
            self._add_edge(body_node, while_node, "Repeat", cluster=cluster, style="dotted")

            # Exit point when condition is False
            exit_node = self._add_node("While End", "circle", cluster=cluster, prefix="while_end")
            self._add_edge(while_node, exit_node, "False", cluster=cluster)
            return exit_node

        # 7) Return statement
        elif isinstance(node, ast.Return):
            return_value = ast.unparse(node.value) if node.value else "None"
            return_node = self._add_node(f"Return: {return_value}", "box", cluster=cluster, prefix="return")
            self._add_edge(current_node, return_node, cluster=cluster, label=edge_label)
            return_points.append(return_node)
            return return_node

        # 8) Other cases
        else:
            return current_node

    def generate_flowchart(self, output_file="code_flowchart"):
        # Start node
        start_node = self._add_node("Start", "ellipse", cluster=self.main_cluster, prefix="start", rank="source")
        current_node = start_node

        # Group and process top-level statements
        grouped_top_level = self._grouped_statements(self.tree.body)
        for g in grouped_top_level:
            current_node = self._process_node(g, current_node, cluster=self.main_cluster)

        # End node
        end_node = self._add_node("End", "ellipse", cluster=self.main_cluster, prefix="end", rank="sink")
        self._add_edge(current_node, end_node, cluster=self.main_cluster)

        # Add subgraphs
        self.graph.subgraph(self.function_cluster)
        self.graph.subgraph(self.main_cluster)

        # Output DOT file
        dot_file = f"{output_file}.dot"
        with open(dot_file, "w", encoding="utf-8") as file:
            file.write(self.graph.source)
        print(f"DOT file saved as {dot_file}")

        # Render PNG image
        self.graph.render(filename=output_file, format='png', cleanup=True)
        print(f"Flowchart saved as {output_file}.png")

if __name__ == "__main__":
    sample_code = """
def isOdd(num):
    if not num%2==0:
        return True
    else:
        print("It's not odd!!!")
    return False

for i in range(3):
    print(isOdd(i))
"""
    generator = CodeFlowchartGenerator(sample_code)
    generator.generate_flowchart("output")