class Condition:
    def __init__(
        self,
        parent=None,
        entity=None,
        expr=None,
        component=None,
        componentElse=None,
        interval=None,
    ):
        self.parent = parent
        self.entity = entity
        self.condition = self.format_condition(expr)
        print(f"Condition: {self.condition}")
        self.component = component
        self.componentElse = componentElse
        self.interval = interval

        try:
            entityRef = entity.source.connection.__class__.__name__
        except AttributeError:
            entityRef = None  # or "Unknown", or whatever fallback you prefer
        source_map = {
            "MQTTBroker": "broker",
            "AMQPBroker": "broker",
            "RedisBroker": "broker",
            "RESTApi": "rest",
            "Database": "db",
            "MySQL": "db",
            "MongoDB": "db",
        }

        self.sourceOfContent = source_map.get(entityRef, "static")

    def format_attribute_path(self, path):
        """
        This method formats the attribute path for the component.
        It converts the path into a list of indices and attributes.
        For example, if the path is "data[0].value", it will be converted to [0, "value"].
        """
        if type(path) == int or type(path) == str or type(path) == float:
            return path
        if type(path) == bool:
            return "true" if path else "false"

        path_array = []
        for accessor in path.accessors:
            if hasattr(accessor, "index") and accessor.index is not None:
                accessor.index = int(accessor.index)
                path_array.append(accessor.index)
            if hasattr(accessor, "attribute") and accessor.attribute is not None:
                path_array.append(accessor.attribute)
        return path_array

    def format_condition_old(self, condition):
        """
        This method formats the condition for the component.
        It converts the condition into an array and also convert the path into an array.
        For example, if the condition is "data[0].value > 10", it will be converted to [['data', 0, 'value'], ['>'], [10]]".
        """
        if condition is not None:
            condition_array = []
            if hasattr(condition, "left") and condition.left is not None:
                condition_array.append(self.format_attribute_path(condition.left))
            if hasattr(condition, "op") and condition.op is not None:
                condition_array.append(condition.op)
            if hasattr(condition, "right") and condition.right is not None:
                condition_array.append(self.format_attribute_path(condition.right))
            return condition_array

    def format_condition(self, expr):
        """
        Walk the AST (OrExpr, AndExpr, PrimaryExpr, ComparisonExpr)
        and emit nested lists:
        ComparisonExpr → [ left_path, op, right_val ]
        AndExpr        → ['and', left, right]
        OrExpr         → ['or',  left, right]
        PrimaryExpr    → dispatch to .expr or .comp
        """

        if expr is None:
            return None

        node = expr.__class__.__name__

        # 1) PrimaryExpr: either .expr (parentheses) or .comp (a ComparisonExpr)
        if node == "PrimaryExpr":
            # parentheses?
            if getattr(expr, "expr", None) is not None:
                return self.format_condition(expr.expr)
            # bare comparison?
            if getattr(expr, "comp", None) is not None:
                return self.format_condition(expr.comp)
            raise ValueError(f"PrimaryExpr missing both .expr and .comp: {expr}")

        # 2) ComparisonExpr: base case
        if node == "ComparisonExpr":
            left = self.format_attribute_path(expr.left)
            right = self.format_attribute_path(expr.right)
            return [left, expr.op, right]

        # 3) AndExpr: left=PrimaryExpr, optional right=AndExpr
        if node == "AndExpr":
            left_list = self.format_condition(expr.left)
            if getattr(expr, "right", None):
                right_list = self.format_condition(expr.right)
                return ["and", left_list, right_list]
            return left_list

        # 4) OrExpr: left=AndExpr, optional right=OrExpr
        if node == "OrExpr":
            left_list = self.format_condition(expr.left)
            if getattr(expr, "right", None):
                right_list = self.format_condition(expr.right)
                return ["or", left_list, right_list]
            return left_list

        raise ValueError(f"Unsupported node type in format_condition: {node}")
