class Component:
    def __init__(self, parent=None, name=None, entity=None, type=None):
        self.isComponent = True
        self.parent = parent
        self.name = name
        self.entity = entity  # This should point to an Entity
        self.type = type  # This could be Gauge, etc.
        try:
            entityRef = entity.source.__class__.__name__
        except AttributeError:
            entityRef = None  # or "Unknown", or whatever fallback you prefer
        self.sourceOfContent = (
            "broker"
            if entityRef in ("MQTTBroker", "AMQPBroker", "RedisBroker")
            else ("rest" if entityRef == "RESTEndpoint" else "static")
        )

    def __str__(self):
        return self.name


class ComponentType:
    def __init__(self, parent=None, name=None):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name


class Gauge(ComponentType):
    def __init__(self, parent=None, name="Gauge", value=None):
        super().__init__(parent, name)
        self.value = value  # Will be resolved to an Attribute


class Notification(ComponentType):
    def __init__(self, parent=None, name="Notification", type="info", message=None):
        super().__init__(parent, name)
        self.type = type
        self.message = message


class Image(ComponentType):
    def __init__(self, parent=None, name="Image", width=300, height=300, source=None):
        super().__init__(parent, name)
        self.width = width
        self.height = height
        self.source = source


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
    ):
        super().__init__(parent, name)
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.xValue = xValue
        self.yValues = yValues


class Publish(ComponentType):
    def __init__(
        self, parent=None, name="Publish", broker=None, api=None, topic=None, json=None
    ):
        super().__init__(parent, name)
        self.broker = broker
        self.api = api
        self.topic = topic
        self.json = json


class LiveTable(ComponentType):
    def __init__(self, parent=None, name="LiveTable", columns=None):
        super().__init__(parent, name)
        self.columns = columns  # This could be a list of Column objects


class JsonViewer(ComponentType):
    def __init__(self, parent=None, name="JsonViewer", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes


class Text(ComponentType):
    def __init__(self, parent=None, name="Text", content=None):
        super().__init__(parent, name)
        self.content = content


class Logs(ComponentType):
    def __init__(self, parent=None, name="Logs", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes
