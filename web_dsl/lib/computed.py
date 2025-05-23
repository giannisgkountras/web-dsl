class ComputedAttribute:
    def __init__(
        self,
        name=None,
        parent=None,
        type=None,
        computed=None,
    ):
        self.name = name
        self.parent = parent
        self.type = type
        self.raw_computed_node = computed
        self.javascript_expression = None
        # self.generator = JSExpressionGenerator()

        if computed and hasattr(computed, "expr"):
            self.javascript_expression = self.format_expression_ast(computed.expr)
            print(self.javascript_expression)
            # self.formatted_expr = self._format_expression_ast(computed.expr)
        else:
            self.javascript_expression = ""

    def format_expression_ast(self, node):
        """
        Recursively formats the expression AST into a nested list structure.
        e.g., x + y  -> ['+', 'x', 'y']
              x * y + z -> ['+', ['*', 'x', 'y'], 'z']
              sum(a, b) -> ['sum', 'a', 'b']
        """
        if node is None:
            return None

        node_class_name = node.__class__.__name__

        if node_class_name == "AddExpr" or node_class_name == "MulExpr":

            current_expr_list = self.format_expression_ast(node.left)

            if hasattr(node, "op") and node.op:  # Check if there are operations
                for i in range(len(node.op)):
                    operator = node.op[i]
                    right_operand = self.format_expression_ast(node.right[i])
                    # Change from tuple to list here:
                    current_expr_list = [operator, current_expr_list, right_operand]
            return current_expr_list

        elif node_class_name == "Atom":
            if node.expr is not None:
                return self.format_expression_ast(node.expr)

            elif node.function is not None:
                return self.format_expression_ast(node.function)

            elif node.id is not None:
                return self.format_attribute_path(node.id)

            elif node.number is not None:
                return node.number
            else:
                raise ValueError(f"Unknown Atom structure: {node.__dict__}")

        elif node_class_name == "FunctionCall":
            function_name = node.name  # This is a string 'sum', 'mean', etc.
            formatted_args = [self.format_expression_ast(arg) for arg in node.args]

            # e.g., ['sum', 'arg1_formatted', 'arg2_formatted']
            return [function_name, *formatted_args]

        elif node_class_name == "RawAccessPathComp":
            # This is a raw access path, e.g., data[0].value
            # We need to format it into a list of indices and attributes
            path = self.format_attribute_path(node.path)
            return path
        raise ValueError(
            f"Unsupported AST node type for expression formatting: {node_class_name} with attributes {node.__dict__}"
        )

    def format_attribute_path(self, path):
        """
        This method formats the attribute path for the component.
        It converts the path into a list of indices and attributes.
        For example, if the path is "data[0].value", it will be converted to [0, "value"].
        """
        if type(path) == int:
            return path

        path_array = []

        path_array.append(path.base)

        for accessor in path.accessors:
            if hasattr(accessor, "index") and accessor.index is not None:
                accessor.index = int(accessor.index)
                path_array.append(accessor.index)
            if hasattr(accessor, "attribute") and accessor.attribute is not None:
                path_array.append(accessor.attribute)
        return path_array


class Atom:
    def __init__(self, parent, number=None, id=None, function=None, expr=None):
        self.parent = parent

        # Store raw inputs from TextX to avoid confusion with instance attributes
        _raw_number = number
        _raw_id = id
        _raw_function = function
        _raw_expr = expr

        # Default all instance attributes to None initially
        self.number = None
        self.id = None
        self.function = None
        self.expr = None

        # Determine the actual matched part of the Atom rule
        # Check in an order that prioritizes more complex/specific types
        if _raw_expr is not None:
            self.expr = _raw_expr

        elif _raw_function is not None:
            self.function = _raw_function

        elif _raw_id is not None and _raw_id != "":
            self.id = _raw_id

        elif _raw_number is not None or (
            _raw_id == "" and _raw_function is None and _raw_expr is None
        ):
            self.number = _raw_number
        else:
            print("Atom unexpected")
