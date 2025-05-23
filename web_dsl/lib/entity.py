class Entity:
    def __init__(
        self,
        name=None,
        parent=None,
        description=None,
        attributes=None,
        strict=None,
        interval=None,
        source=None,
        overloads=None,
    ):
        self.name = name
        self.parent = parent
        self.description = description
        self.attributes = attributes
        self.strict = strict
        self.source = source
        self.interval = interval or 0
        self.overloads = overloads

        # Keep properties of old entity if this entity overloads and they were not provided
        if overloads is not None:
            if source is None:
                self.source = overloads.source
            if attributes is None:
                self.attributes = overloads.attributes
            if strict is None:
                self.strict = overloads.strict
            if interval is None:
                self.interval = overloads.interval

        self.source_classname = self.source.connection.__class__.__name__

        source_map = {
            "MQTTBroker": "broker",
            "AMQPBroker": "broker",
            "RedisBroker": "broker",
            "RESTApi": "rest",
            "Database": "db",
            "MySQL": "db",
            "MongoDB": "db",
        }

        self.sourceOfContent = source_map.get(self.source_classname, "static")

        self.restData = {}
        self.dbData = {}
        self.topic = ""

        if self.sourceOfContent == "rest":
            self.restData = {
                "name": self.source.connection.name,
                "path": getattr(self.source, "path", ""),
                "method": getattr(self.source, "method", None) or "GET",
                "params": getattr(self.source, "params", {}) or {},
            }
        elif self.sourceOfContent == "db":
            connection = getattr(self.source, "connection", "")
            self.dbData = {
                "connection_name": getattr(connection, "name", "default"),
                "database": getattr(connection, "database", ""),
                "query": getattr(self.source, "query", {}) or {},
                "filter": getattr(self.source, "filter", {}) or {},
                "collection": getattr(self.source, "collection", ""),
            }
        elif self.sourceOfContent == "broker":
            self.topic = source.topic
