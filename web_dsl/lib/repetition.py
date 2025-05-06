class Repetition:
    def __init__(
        self,
        parent=None,
        entity=None,
        item=None,
        component=None,
        data=None,
        condition=None,
    ):

        self.parent = parent
        self.entity = entity
        self.item = self.format_attribute_path(item)
        if data is not None:
            self.data = self.format_attribute_path(data)
        else:
            self.data = None
        self.component = component

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
        self.condition = self.format_condition(condition)

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

    def format_condition(self, condition):
        """
        This method formats the condition for the repetition.
        It converts the condition into an array and also convert the path into an array.
        For example, if the condition is "data[0].value > 10", it will be converted to [['data', 0, 'value'], ['>'], [10]]".
        Here we use Half Expression
        """
        if condition is not None:
            # WE INITIALIZE THE CONDITION ARRAY WITH ONE ELEMENT BECAUSE WE WILL USE HALF EXPRESSION
            condition_array = [""]
            if hasattr(condition, "op") and condition.op is not None:
                condition_array.append(condition.op)
            if hasattr(condition, "right") and condition.right is not None:
                condition_array.append(self.format_attribute_path(condition.right))
            return condition_array
