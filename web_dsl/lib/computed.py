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
        print(parent)
        self.type = type
        self.raw_computed_node = computed
        self.javascript_expression = None

        if computed and hasattr(computed, "expr"):
            generator = JSExpressionGenerator()
            self.javascript_expression = generator.to_javascript(computed.expr)
            print(self.javascript_expression)
            # self.formatted_expr = self._format_expression_ast(computed.expr)
        else:
            self.formatted_expr = None

    def _format_expression_ast(self, node):
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

            current_expr_list = self._format_expression_ast(node.left)

            if hasattr(node, "op") and node.op:  # Check if there are operations
                for i in range(len(node.op)):
                    operator = node.op[i]
                    right_operand = self._format_expression_ast(node.right[i])
                    # Change from tuple to list here:
                    current_expr_list = [operator, current_expr_list, right_operand]
            return current_expr_list

        elif node_class_name == "Atom":
            if node.expr is not None:
                return self._format_expression_ast(node.expr)

            elif node.function is not None:
                return self._format_expression_ast(node.function)

            elif node.id is not None:
                return node.id

            elif node.number is not None:
                return node.number
            else:
                raise ValueError(f"Unknown Atom structure: {node.__dict__}")

        elif node_class_name == "FunctionCall":
            function_name = node.name  # This is a string 'sum', 'mean', etc.
            formatted_args = [self._format_expression_ast(arg) for arg in node.args]

            # e.g., ['sum', 'arg1_formatted', 'arg2_formatted']
            return [function_name, *formatted_args]

        raise ValueError(
            f"Unsupported AST node type for expression formatting: {node_class_name} with attributes {node.__dict__}"
        )


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


class JSExpressionGenerator:
    def to_javascript(self, node):
        if node is None:
            return "null"  # Or handle appropriately

        node_class_name = node.__class__.__name__

        if node_class_name == "AddExpr" or node_class_name == "MulExpr":
            # TextX parses 'a + b + c' as:
            # left=a, op=['+', '+'], right=[b, c]
            # We want to reconstruct it as ((a + b) + c)

            js_expr = self.to_javascript(node.left)

            if hasattr(node, "op") and node.op:
                for i in range(len(node.op)):
                    operator = node.op[i]
                    right_operand_js = self.to_javascript(node.right[i])
                    # Ensure correct operator precedence with parentheses if necessary,
                    # though for simple +,-,*,/ left-to-right is usually fine.
                    js_expr = f"({js_expr} {operator} {right_operand_js})"
            return js_expr

        elif node_class_name == "Atom":
            if hasattr(node, "number") and node.number is not None:
                return str(node.number)
            # elif hasattr(node, 'id') and node.id is not None: # Old 'id=ID'
            #     # For simple IDs, assume they are JS variables
            #     return str(node.id)
            elif (
                hasattr(node, "id") and node.id is not None
            ):  # New 'id=AtomReferencable'
                # node.id is now an AtomReferencable (which could be ID or RawAccessPath)
                return self.to_javascript_atom_referencable(node.id)
            elif hasattr(node, "function") and node.function is not None:
                return self.to_javascript(node.function)
            elif (
                hasattr(node, "expr") and node.expr is not None
            ):  # Parenthesized expression
                # The parentheses in the DSL are for grouping, JS will handle its own
                return self.to_javascript(node.expr)  # JS string from inner expr
            else:
                raise ValueError(f"Unknown Atom structure for JS: {node.__dict__}")

        elif node_class_name == "FunctionCall":
            # Map your DSL function names to JavaScript equivalents
            # This is a simple example; you might have a more complex mapping
            js_function_name_map = {
                "sum": "customMath.sum",  # Assuming you have a customMath object in JS
                "mean": "customMath.mean",
                "max": "Math.max",
                "min": "Math.min",
            }
            dsl_func_name = node.name
            js_func_name = js_function_name_map.get(dsl_func_name)
            if not js_func_name:
                raise ValueError(f"Unsupported DSL function for JS: {dsl_func_name}")

            js_args = [self.to_javascript(arg) for arg in node.args]
            return f"{js_func_name}({', '.join(js_args)})"

        # Handling AtomReferencable (which can be ID or RawAccessPath)
        # This method would be called from Atom's 'id' branch
        elif node_class_name == "ID":  # If AtomReferencable resolves to a simple ID
            return str(node)  # Assuming the ID node from TextX is directly the string

        elif node_class_name == "RawAccessPathComp":
            # Example: 'x.test' should become something like 'data.x.test' or 'item.x.test'
            # depending on your JS context.
            # 'x[0].name' -> 'data.x[0].name'
            path_parts = []
            path_parts.append(f"{node.base}")  # This is the base object, e.g., 'data'
            # 'base' is implicit here, you'll add it in the JS function call context
            for accessor_node in node.accessors:
                if accessor_node.__class__.__name__ == "AttributeAccessorComp":
                    path_parts.append(f".{accessor_node.attribute}")
                elif accessor_node.__class__.__name__ == "IndexAccessorComp":
                    path_parts.append(f"[{accessor_node.index}]")
            # This will return something like ".attr1[0].attr2"
            # The initial variable (e.g., 'data') will be prepended in the template.
            return "".join(
                path_parts
            )  # Will be like ".property" or "[0]" or ".prop[0]"

        # Handle Expr if it's ever passed directly (unlikely with Expr: AddExpr;)
        elif node_class_name == "Expr":
            return self.to_javascript(node.left)  # Or however Expr is structured

        raise ValueError(f"Unsupported AST node for JS: {node_class_name}")

    def to_javascript_atom_referencable(self, atom_ref_node):
        # atom_ref_node is the object assigned to Atom.id
        # Based on your specialization, it will be an instance of RawAccessPath or an ID string
        if isinstance(atom_ref_node, str):  # If it's a direct ID string
            return atom_ref_node
        else:  # It's an object, like RawAccessPath instance
            # We need to dispatch to the correct handler based on its actual class
            # The main to_javascript method will handle RawAccessPath if called with it.
            return self.to_javascript(atom_ref_node)
