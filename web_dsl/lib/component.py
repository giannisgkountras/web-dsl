from textx.exceptions import TextXSemanticError


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
        if not self.value:  # Skip if no value is specified
            return

        if not hasattr(self.value, "obj_name"):  # If value isn't a reference
            return

        attr_name = self.value.obj_name
        component = self.parent

        if not component or not component.refersTo:
            raise TextXSemanticError(
                f"Component '{component.name if component else 'unknown'}' has no refersTo entity defined"
            )

        entity = component.refersTo

        if not hasattr(entity, "attributes"):
            raise TextXSemanticError(
                f"Entity '{entity.name}' has no attributes defined"
            )

        for attr in entity.attributes:
            if attr.name == attr_name:
                self.value = attr
                return

        raise TextXSemanticError(
            f"Attribute '{attr_name}' not found in Entity '{entity.name}'"
        )
