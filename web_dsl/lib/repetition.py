class Repetition:
    def __init__(
        self,
        parent=None,
        item=None,
        component=None,
        data=None,
        expr=None,
        componentElse=None,
        componentRef=None,
        componentElseRef=None,
        dataElse=None,
        orientation=None,
    ):

        self.entities = set()
        self.parent = parent
        self.raw_item = item

        self.raw_data = data

        self.raw_dataElse = dataElse

        if componentRef is not None:
            self.component = componentRef
        else:
            self.component = component

        if componentElseRef is not None:
            self.componentElse = componentElseRef
        else:
            self.componentElse = componentElse

        if orientation is None:
            self.orientation = "row"
        else:
            self.orientation = orientation

        self.raw_expr = expr

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

        if hasattr(path, "entity") and path.entity is not None:
            self.entities.add(path.entity)
            path_array.append(path.entity.name)

        for accessor in path.accessors:
            if hasattr(accessor, "index") and accessor.index is not None:
                accessor.index = int(accessor.index)
                path_array.append(accessor.index)
            if hasattr(accessor, "attribute") and accessor.attribute is not None:
                path_array.append(accessor.attribute)
        return path_array

    def format_condition(self, condition):
        """
        This method formats the condition for the repetition.
        It converts the condition into an array and also convert the path into an array.
        For example, if the condition is "data[0].value > 10", it will be converted to [['data', 0, 'value'], ['>'], [10]]".
        Here we use Half Expression
        """
        if condition is not None:
            condition_array = []
            if hasattr(condition, "left") and condition.op is not None:
                condition_array.append(self.format_attribute_path(condition.left))
            if hasattr(condition, "op") and condition.op is not None:
                condition_array.append(condition.op)
            if hasattr(condition, "right") and condition.right is not None:
                condition_array.append(self.format_attribute_path(condition.right))
            return condition_array
