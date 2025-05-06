class Repetition:
    def __init__(self, parent=None, entity=None, item=None, component=None, data=None):

        self.parent = parent
        self.entity = entity
        self.item = self.format_attribute_path(item)
        if data is not None:
            self.data = self.format_attribute_path(data)
        else:
            self.data = None
        self.component = component

        print(f"Repetition: {self.component} - {self.item}")
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
