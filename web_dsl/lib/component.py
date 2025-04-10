from textx.exceptions import TextXSemanticError


def resolve_reference(
    self, ref_attr="value", target_collection_attr="attributes", target_item_attr="name"
):
    """
    Generic reference resolver.

    - ref_attr: the name of the field on self that holds a reference (default "value")
    - target_collection_attr: the name of the collection on the referred-to entity to search (default "attributes")
    - target_item_attr: the attribute of items in that collection used for matching (default "name")

    This method looks for an object reference inside self.<ref_attr> that has an attribute 'obj_name'.
    It then finds the parent component's entity and searches its target_collection for an item
    where the target_item_attr equals the ref's obj_name. If found, it replaces self.<ref_attr> with that item.
    """
    ref = getattr(self, ref_attr, None)
    if not ref or not hasattr(ref, "obj_name"):
        return  # Nothing to resolve

    ref_name = ref.obj_name
    parent = getattr(self, "parent", None)
    if not parent or not getattr(parent, "entity", None):
        raise TextXSemanticError(
            f"Component '{getattr(parent, 'name', 'unknown')}' has no entity defined"
        )
    entity = parent.entity

    if not hasattr(entity, target_collection_attr):
        raise TextXSemanticError(
            f"Entity '{entity.name}' has no {target_collection_attr} defined"
        )

    collection = getattr(entity, target_collection_attr)
    found = next(
        (
            item
            for item in collection
            if getattr(item, target_item_attr, None) == ref_name
        ),
        None,
    )
    if found:
        setattr(self, ref_attr, found)
    else:
        raise TextXSemanticError(
            f"Item '{ref_name}' not found in Entity '{entity.name}'"
        )


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


# class ComponentRef:
#     def __init__(self, ref=None, parent=None, name=None):
#         self.isComponent = True
#         self.parent = parent
#         self.name = name
#         self.entity = ref.entity  # This should point to an Entity
#         self.type = ref.type  # This could be Gauge, etc.
#         try:
#             print(
#                 f"I AM A REFERENCE COMPONENT TO {ref.name} with {ref.entity} and {ref.entity.source.__class__.__name__}"
#             )
#             entityRef = ref.entity.source.__class__.__name__
#         except AttributeError:
#             entityRef = None  # or "Unknown", or whatever fallback you prefer
#         self.sourceOfContent = (
#             "broker"
#             if entityRef == "MessageBroker"
#             else ("rest" if entityRef == "RESTEndpoint" else "static")
#         )

#     def __str__(self):
#         return self.name


class ComponentType:
    def __init__(self, parent=None, name=None):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name

    def resolve_references(self):
        pass  # Subclasses override this


class Gauge(ComponentType):
    def __init__(self, parent=None, name="Gauge", value=None):
        super().__init__(parent, name)
        self.value = value  # Will be resolved to an Attribute

    def resolve_references(self):
        # Here, we assume that Gauge's 'value' should resolve from the parent's
        # entity's attributes. For a different component, you might
        # pass different parameters (e.g. 'message', 'price', etc.).
        resolve_reference(self)


class Notification(ComponentType):
    def __init__(self, parent=None, name="Notification", type="info", message=None):
        super().__init__(parent, name)
        self.type = type
        self.message = message

    def resolve_references(self):
        resolve_reference(self, ref_attr="message")


class Image(ComponentType):
    def __init__(self, parent=None, name="Image", width=300, height=300, source=None):
        super().__init__(parent, name)
        self.width = width
        self.height = height
        self.source = source

    def resolve_references(self):
        resolve_reference(self, ref_attr="source")


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

    def resolve_references(self):
        resolve_reference(self, ref_attr="xValue")
        # Assuming yValue is a list of references, we might need to resolve each one
        if isinstance(self.yValues, list):
            for item in self.yValues:
                resolve_reference(item, ref_attr="yValues")
        else:
            resolve_reference(self, ref_attr="yValues")


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

        if isinstance(self.columns, list):
            for item in self.columns:
                resolve_reference(item, ref_attr="columns")
        else:
            resolve_reference(self, ref_attr="columns")


class JsonViewer(ComponentType):
    def __init__(self, parent=None, name="JsonViewer", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes

        resolve_reference(self, ref_attr="attributes")


class Text(ComponentType):
    def __init__(self, parent=None, name="Text", content=None):
        super().__init__(parent, name)
        self.content = content


class Logs(ComponentType):
    def __init__(self, parent=None, name="Logs", attributes=None):
        super().__init__(parent, name)
        self.attributes = attributes
        resolve_reference(self, ref_attr="attributes")
