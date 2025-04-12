from pymongo import MongoClient
import pymysql
import logging


class DBConnector:
    def __init__(self, config):
        self.connections = {}
        self._initialize_connections(config)

    def _initialize_connections(self, config):
        # Handle MySQL configurations
        mysql_configs = config.get("mysql") or []
        for mysql_config in mysql_configs:
            self._connect_mysql(mysql_config)

        # Handle MongoDB configurations
        mongo_configs = config.get("mongo") or []
        for mongo_config in mongo_configs:
            self._connect_mongo(mongo_config)

    def _connect_mysql(self, cfg):
        try:
            connection = pymysql.connect(
                host=cfg.get("host"),
                port=cfg.get("port", 3306),
                user=cfg.get("user"),
                password=cfg.get("password"),
                # No default database is selected here
                cursorclass=pymysql.cursors.DictCursor,
            )
            # Use the connection name directly as the key
            conn_name = cfg.get("name")
            self.connections[conn_name] = connection
            print(f"✅ MySQL connected to {conn_name}")
        except Exception as e:
            print(f"❌ MySQL connection error for {cfg.get('name')}: {e}")

    def _connect_mongo(self, cfg):
        try:
            # Build the MongoDB URI
            mongo_uri = (
                f"mongodb://{cfg.get('user')}:{cfg.get('password')}@"
                f"{cfg.get('host')}:{cfg.get('port')}/?authSource={cfg.get('authSource', 'admin')}"
            )
            client = MongoClient(mongo_uri)
            # Here the connection name is used as the name for the MongoDB database
            conn_name = cfg.get("name")
            db = client[conn_name]
            self.connections[conn_name] = db
            print(f"✅ MongoDB connected to {conn_name}")
        except Exception as e:
            print(f"❌ MongoDB connection error for {cfg.get('name')}: {e}")

    # ----------------------
    # MySQL operations
    # ----------------------
    def mysql_query(self, connection_name, database, query, params=None):
        """
        Executes a MySQL query on the connection identified by connection_name.
        You must provide the target database and table. The method switches to the specified
        database using connection.select_db(database) before executing the query.

        The query string can include the placeholder `{table}`, which gets replaced by the
        provided table name.

        Example:
            query = "SELECT * FROM {table} WHERE id = %s"
        """
        connection = self.connections.get(connection_name)
        if connection is None:
            print(f"❌ No MySQL connection for {connection_name}")
            return None

        try:
            # Switch to the specified database
            connection.select_db(database)

            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return results

        except Exception as e:
            print(
                f"❌ MySQL query error on connection '{connection_name}', database '{database}': {e}"
            )
            return None

    # ----------------------
    # MongoDB operations
    # ----------------------
    def mongo_find(self, connection_name, collection, filter=None):
        """
        Executes a find operation on the MongoDB connection identified by connection_name.
        'collection' here is analogous to a table in SQL.
        """
        db = self.connections.get(connection_name)
        if db is None:
            print(f"❌ No MongoDB connection for {connection_name}")
            return None
        try:
            return list(db[collection].find(filter or {}))
        except Exception as e:
            print(
                f"❌ Mongo find error on connection '{connection_name}', collection '{collection}': {e}"
            )
            return None

    def mongo_insert(self, connection_name, collection, document):
        db = self.connections.get(connection_name)
        if db is None:
            print(f"❌ No MongoDB connection for {connection_name}")
            return None
        try:
            return db[collection].insert_one(document).inserted_id
        except Exception as e:
            print(
                f"❌ Mongo insert error on connection '{connection_name}', collection '{collection}': {e}"
            )
            return None

    def mongo_update(self, connection_name, collection, filter, update):
        db = self.connections.get(connection_name)
        if db is None:
            print(f"❌ No MongoDB connection for {connection_name}")
            return None
        try:
            result = db[collection].update_many(filter, {"$set": update})
            return result.modified_count
        except Exception as e:
            print(
                f"❌ Mongo update error on connection '{connection_name}', collection '{collection}': {e}"
            )
            return None

    def mongo_delete(self, connection_name, collection, filter):
        db = self.connections.get(connection_name)
        if db is None:
            print(f"❌ No MongoDB connection for {connection_name}")
            return None
        try:
            result = db[collection].delete_many(filter)
            return result.deleted_count
        except Exception as e:
            print(
                f"❌ Mongo delete error on connection '{connection_name}', collection '{collection}': {e}"
            )
            return None
