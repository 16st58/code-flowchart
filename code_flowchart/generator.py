import ast
from graphviz import Digraph

class CodeFlowchartGenerator:
    """
    주어진 Python 소스 코드를 파싱(AST)하여
    순서도를(Flowchart) 자동 생성해주는 클래스.
    Graphviz를 이용해 PNG 이미지, DOT 파일을 생성합니다.
    """

    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)
        self.graph = Digraph(format='png')
        self.graph.attr(rankdir="TB")  # Top-to-Bottom layout
        self.graph.attr(nodesep="0.5", ranksep="0.75")  # 노드 및 랭크 간 간격
        self.graph.attr(size="10,10", dpi="300")  # 출력 이미지 사이즈 & 해상도
        self.counter = 0  # 노드 ID 카운터
        self.function_definitions = {}
        self.function_flow_nodes = {}
        self.node_prefix_map = {}  # 각 노드 ID에 대한 prefix 관리

        # 메인 흐름을 담을 서브그래프
        self.main_cluster = Digraph(name="cluster_main")
        self.main_cluster.attr(label="Main Code", fontsize="16", style="dashed", color="blue")

        # 함수 정의를 담을 서브그래프
        self.function_cluster = Digraph(name="cluster_functions")
        self.function_cluster.attr(label="Functions", fontsize="16", style="dashed", color="green")

        # 함수 정의를 미리 수집
        self._gather_function_definitions(self.tree)

    def _get_unique_id(self, prefix="node"):
        """prefix를 포함한 유니크한 노드 ID를 생성."""
        self.counter += 1
        node_id = f"{prefix}_{self.counter}"
        self.node_prefix_map[node_id] = prefix
        return node_id

    def _add_node(self, label, shape="box", cluster=None, prefix="node", rank="same"):
        """그래프(혹은 서브그래프)에 노드를 추가하고 노드의 ID를 반환."""
        node_id = self._get_unique_id(prefix)
        if cluster:
            cluster.node(node_id, label, shape=shape, fontsize="12")
        else:
            self.graph.node(node_id, label, shape=shape, fontsize="12")

        # rank 설정
        if rank:
            self.graph.body.append(f'{{rank={rank}; "{node_id}";}}')

        return node_id

    def _add_edge(self, from_node, to_node, label="", cluster=None, color="black", style="solid"):
        """그래프(혹은 서브그래프)에 엣지를 추가."""
        if cluster:
            cluster.edge(from_node, to_node, label=label, fontsize="10", color=color, style=style)
        else:
            self.graph.edge(from_node, to_node, label=label, fontsize="10", color=color, style=style)

    def _get_node_prefix(self, node_id):
        """노드 ID에 대응하는 prefix를 반환."""
        return self.node_prefix_map.get(node_id, "unknown")

    def _gather_function_definitions(self, node: ast.AST):
        """AST 전체를 순회하여 함수 정의(ast.FunctionDef)만 미리 수집."""
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef):
                self.function_definitions[child.name] = child

    def _is_major_statement(self, stmt: ast.stmt):
        """
        '주요 구문' 여부 판별.
        - if, for, while, function def, return
        - 사용자 정의 함수 호출
        """
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.FunctionDef, ast.Return)):
            return True

        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func_name = None
            try:
                func_name = ast.unparse(stmt.value.func)
            except Exception:
                pass

            # 사용자 정의 함수명인지 확인
            if func_name and func_name in self.function_definitions:
                return True

        return False

    def _grouped_statements(self, stmts):
        """
        구문 리스트를 순회하며 주요 구문을 단독 처리,
        그 외 연속된 minor 구문들을 하나의 그룹(list)으로 묶어서 반환.
        
        예:
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
        여러 statement(또는 statement 그룹)을 순서대로 처리해
        마지막 노드를 반환한다.
        """
        if return_points is None:
            return_points = []

        current_node = start_node
        grouped = self._grouped_statements(stmts)

        for group in grouped:
            current_node = self._process_node(group, current_node, cluster=cluster, return_points=return_points)

        return current_node

    def _process_node(self, node, current_node, cluster=None, return_points=None, edge_label=""):
        """
        AST 노드(또는 노드 리스트)를 받아서
        대응되는 Flow 차트 노드를 생성, 연결 후 다음 노드를 반환.
        """
        if return_points is None:
            return_points = []

        # 1) 여러 minor statements가 묶인 list
        if isinstance(node, list):
            expr_node = self._add_node("Expression", "box", cluster=cluster, prefix="expr")
            self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)
            return expr_node

        # 2) FunctionDef(함수 정의)
        elif isinstance(node, ast.FunctionDef):
            # 함수 정의 노드는 메인 코드 흐름 상에서 그냥 지나침.
            return current_node

        # 3) Expression(함수 호출/단순 표현식 등)
        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                func_name = ast.unparse(node.value.func)
                expr_content = ast.unparse(node.value)
                if func_name in self.function_definitions:
                    # 사용자 정의 함수 호출
                    expr_node = self._add_node(f"Call: {expr_content}", "box", cluster=cluster, prefix="call")
                    self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)

                    func_def = self.function_definitions[func_name]
                    if func_name in self.function_flow_nodes:
                        func_start_node, func_end_node, _ = self.function_flow_nodes[func_name]
                    else:
                        func_start_node = self._add_node(f"Function: {func_name}", "ellipse",
                                                         cluster=self.function_cluster, prefix="function")
                        func_body_node = func_start_node
                        func_return_points = []

                        # 함수 본문 처리
                        func_body_node = self._process_body(func_def.body, self.function_cluster, func_body_node, func_return_points)
                        func_end_node = func_body_node

                        self.function_flow_nodes[func_name] = (func_start_node, func_end_node, func_return_points)

                    # 메인 클러스터에서 함수 호출 노드 -> 함수 시작 노드로 점선(edge) 연결
                    self._add_edge(expr_node, func_start_node, label="Call", cluster=self.main_cluster, style="dashed")

                    # 함수 내부 return 지점들 -> 호출 노드로 복귀 점선(edge)
                    for return_node in self.function_flow_nodes[func_name][2]:
                        self._add_edge(return_node, expr_node, label="Return", style="dashed")

                    return expr_node
                else:
                    # 외부 함수 호출 혹은 라이브러리 함수 호출
                    expr_node = self._add_node(f"Expression: {expr_content}", "box", cluster=cluster, prefix="expr")
                    self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)
                    return expr_node
            else:
                # 단순 표현식
                expr_content = ast.unparse(node.value)
                expr_node = self._add_node(f"Expression: {expr_content}", "box", cluster=cluster, prefix="expr")
                self._add_edge(current_node, expr_node, cluster=cluster, label=edge_label)
                return expr_node

        # 4) If
        elif isinstance(node, ast.If):
            condition = ast.unparse(node.test)
            if_node = self._add_node(f"If: {condition}", "diamond", cluster=cluster, prefix="if")
            self._add_edge(current_node, if_node, cluster=cluster)

            body_node = if_node
            if_end_node = body_node
            is_first_true_edge = True

            # if 본문
            grouped_body = self._grouped_statements(node.body)
            for g in grouped_body:
                edge_label_for_body = "True" if is_first_true_edge else ""
                if_end_node = self._process_node(g, if_end_node, cluster=cluster, return_points=return_points,
                                                 edge_label=edge_label_for_body)
                is_first_true_edge = False

            end_nodes = [if_end_node]

            # else / elif 처리
            if node.orelse:
                first_else_node = node.orelse[0] if node.orelse else None
                if isinstance(first_else_node, ast.If):
                    # Elif인 경우
                    elif_end_node = self._process_node(
                        first_else_node, if_node, cluster=cluster, return_points=return_points, edge_label="False"
                    )
                    # 첫 elif의 나머지 else 구문은 first_else_node.orelse로 처리됨
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

            # If 종료(merge) 지점
            merge_node = self._add_node("If End", "circle", cluster=cluster, prefix="if_end")
            for end_node in end_nodes:
                if self._get_node_prefix(end_node) != "return":  # return 노드는 merge로 연결 안 함
                    self._add_edge(end_node, merge_node, cluster=cluster)

            return merge_node

        # 5) For
        elif isinstance(node, ast.For):
            target = ast.unparse(node.target)
            iter_ = ast.unparse(node.iter)
            for_node = self._add_node(f"For: {target} in {iter_}", "box", cluster=cluster, prefix="for")
            self._add_edge(current_node, for_node, cluster=cluster)

            # for 루프 본문
            body_node = for_node
            body_node = self._process_body(node.body, cluster, body_node, return_points)

            # 루프 반복(마지막에서 다시 for_node로)
            self._add_edge(body_node, for_node, "Repeat", cluster=cluster, style="dotted")
            return for_node

        # 6) While
        elif isinstance(node, ast.While):
            condition = ast.unparse(node.test)
            while_node = self._add_node(f"While: {condition}", "diamond", cluster=cluster, prefix="while")
            self._add_edge(current_node, while_node, cluster=cluster)

            # while 본문
            body_node = while_node
            body_node = self._process_body(node.body, cluster, body_node, return_points)

            # 반복
            self._add_edge(body_node, while_node, "Repeat", cluster=cluster, style="dotted")

            # False일 때 탈출
            exit_node = self._add_node("While End", "circle", cluster=cluster, prefix="while_end")
            self._add_edge(while_node, exit_node, "False", cluster=cluster)
            return exit_node

        # 7) Return
        elif isinstance(node, ast.Return):
            return_value = ast.unparse(node.value) if node.value else "None"
            return_node = self._add_node(f"Return: {return_value}", "box", cluster=cluster, prefix="return")
            self._add_edge(current_node, return_node, cluster=cluster, label=edge_label)
            return_points.append(return_node)
            return return_node

        # 8) 기타
        else:
            return current_node

    def generate_flowchart(self, output_file="code_flowchart"):
        # Start 노드
        start_node = self._add_node("Start", "ellipse", cluster=self.main_cluster, prefix="start", rank="source")
        current_node = start_node

        # 최상위 레벨 구문을 그룹화 처리
        grouped_top_level = self._grouped_statements(self.tree.body)
        for g in grouped_top_level:
            current_node = self._process_node(g, current_node, cluster=self.main_cluster)

        # End 노드
        end_node = self._add_node("End", "ellipse", cluster=self.main_cluster, prefix="end", rank="sink")
        self._add_edge(current_node, end_node, cluster=self.main_cluster)

        # 서브그래프 추가
        self.graph.subgraph(self.function_cluster)
        self.graph.subgraph(self.main_cluster)

        # DOT 파일 출력
        dot_file = f"{output_file}.dot"
        with open(dot_file, "w", encoding="utf-8") as file:
            file.write(self.graph.source)
        print(f"DOT file saved as {dot_file}")

        # PNG 이미지 렌더
        self.graph.render(filename=output_file, format='png', cleanup=True)
        print(f"Flowchart saved as {output_file}.png")
