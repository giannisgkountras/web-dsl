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

    def format_attribute_path(self, path):
        """
        This method formats the attribute path for the component.
        It converts the path into a list of indices and attributes.
        For example, if the path is "data[0].value", it will be converted to [0, "value"].
        """
        if type(path) == int:
            return path

        path_array = []

        for accessor in path.accessors:
            if hasattr(accessor, "index") and accessor.index is not None:
                accessor.index = int(accessor.index)
                path_array.append(accessor.index)
            if hasattr(accessor, "attribute") and accessor.attribute is not None:
                path_array.append(accessor.attribute)
        return path_array


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
    def __init__(
        self, parent=None, name="Gauge", value=None, value_static=None, description=None
    ):
        super().__init__(parent, name)
        if value is not None:
            self.value = self.format_attribute_path(value)
        self.value_static = value_static  # Static value for the gauge
        self.description = description  # Description for the gauge


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
    def __init__(self, parent=None, name="Alive", timeout=5000, description=None):
        super().__init__(parent, name)
        self.timeout = timeout
        self.description = description


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
        description=None,
    ):
        super().__init__(parent, name)
        self.xLabel = xLabel
        self.yLabel = yLabel
        if xValue is not None:
            self.xValue = self.format_attribute_path(xValue)
        if yValues is not None:
            self.yValues = [self.format_attribute_path(yValue) for yValue in yValues]
        self.staticData = staticData
        self.xValue_static = xValue_static
        self.yValues_static = yValues_static
        self.description = description


class BarChart(ComponentType):
    def __init__(
        self,
        parent=None,
        name="BarChart",
        xLabel="X-Axis",
        yLabel="Y-Axis",
        xValue=None,
        yValues=None,
        xValue_static=None,
        yValues_static=None,
        staticData=[],
        description=None,
    ):
        super().__init__(parent, name)
        self.xLabel = xLabel
        self.yLabel = yLabel
        if xValue is not None:
            self.xValue = self.format_attribute_path(xValue)
        if yValues is not None:
            self.yValues = [self.format_attribute_path(yValue) for yValue in yValues]
        self.staticData = staticData
        self.xValue_static = xValue_static
        self.yValues_static = yValues_static
        self.description = description


class PieChart(ComponentType):
    def __init__(
        self,
        parent=None,
        name="PieChart",
        dataName=None,
        value=None,
        dataName_static=None,
        value_static=None,
        staticData=[],
        description=None,
    ):
        super().__init__(parent, name)
        if dataName is not None:
            self.dataName = self.format_attribute_path(dataName)
        if value is not None:
            self.value = self.format_attribute_path(value)
        self.staticData = staticData
        self.dataName_static = dataName_static
        self.value_static = value_static
        self.description = description


class Publish(ComponentType):
    def __init__(
        self,
        parent=None,
        name="Publish",
        broker=None,
        endpoint=None,
        topic=None,
        json=None,
        description=None,
    ):
        super().__init__(parent, name)
        self.broker = broker
        self.endpoint = endpoint
        self.topic = topic
        self.json = json
        self.description = description


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
        if attributes is not None:
            self.attributes = [
                self.format_attribute_path(attribute) for attribute in attributes
            ]


class CrudTable(ComponentType):
    def __init__(
        self, parent=None, name="CrudTable", attributes=None, primary_key=None
    ):
        super().__init__(parent, name)
        self.primary_key = primary_key
        if attributes is not None:
            self.attributes = [
                self.format_attribute_path(attribute) for attribute in attributes
            ]


class Input(ComponentType):
    def __init__(
        self,
        parent=None,
        name="Input",
        type=None,
        placeholder=None,
        required=None,
        datakey=None,
    ):
        super().__init__(parent, name)
        self.type = type
        self.placeholder = placeholder
        self.required = required
        self.datakey = datakey

    def to_dict(self):
        return {
            "kind": "input",
            "type": self.type,
            "placeholder": self.placeholder,
            "required": "true" if self.required else "false",
            "datakey": self.datakey,
        }


class Label(ComponentType):
    def __init__(self, parent=None, name="Label", content=None):
        super().__init__(parent, name)
        self.content = content

    def to_dict(self):
        return {
            "kind": "label",
            "content": self.content,
        }


class Form(ComponentType):
    def __init__(self, parent=None, name="Form", elements=None, description=None):
        super().__init__(parent, name)
        if elements is not None:
            formatted_elements = [el.to_dict() for el in elements]
        else:
            formatted_elements = []
        self.elements = formatted_elements
        self.description = description
