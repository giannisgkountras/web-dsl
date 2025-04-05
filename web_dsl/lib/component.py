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
    It then finds the parent component's 'refersTo' entity and searches its target_collection for an item
    where the target_item_attr equals the ref's obj_name. If found, it replaces self.<ref_attr> with that item.
    """
    ref = getattr(self, ref_attr, None)
    if not ref or not hasattr(ref, "obj_name"):
        return  # Nothing to resolve

    ref_name = ref.obj_name
    parent = getattr(self, "parent", None)
    if not parent or not getattr(parent, "refersTo", None):
        raise TextXSemanticError(
            f"Component '{getattr(parent, 'name', 'unknown')}' has no refersTo entity defined"
        )
    entity = parent.refersTo

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
        self.parent = parent
        self.name = name
        self.entity = entity  # This should point to an Entity
        self.type = type  # This could be Gauge, etc.

    def __str__(self):
        return self.name


class ComponentType:
    def __init__(self, parent=None, name=None):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name

    def resolve_references(self):
        pass  # Subclasses override this


class Gauge(ComponentType):
    def __init__(self, parent=None, name=None, value=None):
        super().__init__(parent, name)
        self.value = value  # Will be resolved to an Attribute

    def resolve_references(self):
        # Here, we assume that Gauge's 'value' should resolve from the parent's
        # refersTo entity's attributes. For a different component, you might
        # pass different parameters (e.g. 'message', 'price', etc.).
        resolve_reference(self)


class Notification(ComponentType):
    def __init__(self, parent=None, name=None, type="info", message=None):
        super().__init__(parent, name)
        self.message = message  # This could be a string or an expression

    def resolve_references(self):
        resolve_reference(self, ref_attr="message")


class Image(ComponentType):
    def __init__(self, parent=None, name=None, width=300, height=300, source=None):
        super().__init__(parent, name)
        self.width = width  # This could be a string or an expression
        self.height = height
        self.source = source
