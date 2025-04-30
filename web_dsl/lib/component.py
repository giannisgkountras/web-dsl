class Component:
    def __init__(self, parent=None, name=None, entity=None, type=None):
        self.isComponent = True
        self.parent = parent
        self.name = name
        self.entity = entity  # This should point to an Entity
        self.type = type  # This could be Gauge, etc.
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

    def __str__(self):
        return self.name


class ComponentType:
    def __init__(self, parent=None, name=None):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name

    def format_attribute_path(self, path):
        """
        This method formats the attribute path for the component.
        It converts the path into a list of indices and attributes.
        For example, if the path is "data[0].value", it will be converted to [0, "value"].
        """
        path_array = []

        for accessor in path.accessors:
            if hasattr(accessor, "index") and accessor.index is not None:
                accessor.index = int(accessor.index)
                path_array.append(accessor.index)
            if hasattr(accessor, "attribute") and accessor.attribute is not None:
                path_array.append(accessor.attribute)
        return path_array


class Gauge(ComponentType):
    def __init__(self, parent=None, name="Gauge", value=None, value_static=None):
        super().__init__(parent, name)
        if value is not None:
            self.value = self.format_attribute_path(value)
        self.value_static = value_static  # Static value for the gauge


class Notification(ComponentType):
    def __init__(self, parent=None, name="Notification", type="info", message=None):
        super().__init__(parent, name)
        self.type = type
        if message is not None:
            self.message = self.format_attribute_path(message)


class Image(ComponentType):
    def __init__(
        self,
        parent=None,
        name="Image",
        width=300,
        height=300,
        source=None,
        source_static=None,
    ):
        super().__init__(parent, name)
        self.width = width
        self.height = height
        if source is not None:
            self.source = self.format_attribute_path(source)
        self.source_static = source_static


class Alive(ComponentType):
    def __init__(self, parent=None, name="Alive", timeout=5000):
        super().__init__(parent, name)
        self.timeout = timeout


class LineChart(ComponentType):
    def __init__(
        self,
        parent=None,
        name="LineChart",
        xLabel="X-Axis",
        yLabel="Y-Axis",
        xValue=None,
        yValues=None,
        xValue_static=None,
        yValues_static=None,
        staticData=[],
    ):
        super().__init__(parent, name)
        self.xLabel = xLabel
        self.yLabel = yLabel
        if xValue is not None:
            self.xValue = self.format_attribute_path(xValue)
        if yValues is not None:
            self.yValues = [self.format_attribute_path(yValue) for yValue in yValues]
        self.staticData = staticData


class Publish(ComponentType):
    def __init__(
        self,
        parent=None,
        name="Publish",
        broker=None,
        endpoint=None,
        topic=None,
        json=None,
    ):
        super().__init__(parent, name)
        self.broker = broker
        self.endpoint = endpoint
        self.topic = topic
        self.json = json


class LiveTable(ComponentType):
    def __init__(self, parent=None, name="LiveTable", columns=None):
        super().__init__(parent, name)
        if columns is not None:
            self.columns = [self.format_attribute_path(column) for column in columns]


class JsonViewer(ComponentType):
    def __init__(self, parent=None, name="JsonViewer", attributes=None):
        super().__init__(parent, name)
        if attributes is not None:
            self.attributes = [
                self.format_attribute_path(attribute) for attribute in attributes
            ]


class Text(ComponentType):
    def __init__(
        self,
        parent=None,
        name="Text",
        content=None,
        content_static=None,
        size=None,
        color="#fff",
    ):
        super().__init__(parent, name)
        if content is not None:
            self.content = self.format_attribute_path(content)
        self.content_static = content_static
        self.size = size
        self.color = color


class Logs(ComponentType):
    def __init__(self, parent=None, name="Logs", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes


class CrudTable(ComponentType):
    def __init__(self, parent=None, name="CrudTable", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes
