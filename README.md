<img src="./web_dsl/assets/web_dsl_logo_4.png" alt="web-dsl" width="800px"/>

[WebDSL](https://giannisgkountras.github.io/web-dsl-page/) is an external Domain-Specific Language (DSL) designed for generating full-stack applications. It integrates multiple data sources, including databases, message brokers, and REST APIs, while also supporting static components. At its core, WebDSL revolves around entities, which are linked to data sources, define the data model, and are utilized by components to visualize data.

The language emphasizes simplicity and ease of use, enabling developers to rapidly build applications without needing to manage low-level implementation details. At the same time, WebDSL is highly extensible, as it generates standard React and FastAPI code, making it easy to incorporate custom logic and advanced features when needed.

A typical WebDSL webpage is composed of connections, data sources, entities, components, and screens. For example, a connection might link to a MongoDB database, with a specific query defined in the data source. An entity then describes the structure of the data, and a component, such as a bar chart, can visualize that data. Screens bring everything together by defining layouts and specifying which components appear.

In summary, WebDSL is a powerful and flexible tool for rapidly developing full-stack applications, with a strong focus on data integration and visualization.

# Table of contents

-   [Installation ](#installation-)
-   [Features](#features)
-   [Usage](#usage)
    -   [Webpage](#webpage)
    -   [Connections](#connections)
    -   [Data Sources](#data-sources)
    -   [Entities](#entities)
    -   [Components](#components)
    -   [Conditions](#conditions)
    -   [Loops](#loops)
    -   [Screens](#screens)
-   [Import](#import)
-   [Validation ](#validation)
-   [Code Generation ](#generation)
-   [OpenAPI Transformation](#open-api)
-   [GoalDSL Transformation](#goal-dsl)
-   [Examples ](#examples)

## Installation <a name="installation"></a>

Download this repository and simply install using `pip` package manager.

```
git clone https://github.com/giannisgkountras/web-dsl
cd web-dsl
pip install .
```

## Features

-   **Declarative Syntax**: Define data sources, entities and components and their relationships in a clear and concise manner.
-   **Extensible**: Easily add custom logic and components to fit your specific use case.
-   **Human-Readable**: Applications are defined in a way that is easy to understand and maintain.

Currently the DSL supports the following types of data sources:

-   **Message Broker**: MQTT, AMQP, Redis
-   **REST API**: REST API
-   **Database**: MongoDB, MySQL
-   **Static**: Static data

And the following types of components:

-   **Text**: Displays static or dynamic text content
-   **Image**: Renders an image from a given source
-   **Bar Chart**: Visualizes data using a bar chart
-   **Line Chart**: Visualizes trends over time with a line chart
-   **Pie Chart**: Displays proportional data in a pie chart format
-   **Table**: Shows structured data in a tabular format, allowind CRUD operations
-   **Live Table**: Real-time table that updates as new data arrives
-   **Form**: Collects user input and submits it to a data source
-   **Notification**: Displays alerts or status messages
-   **Gauge**: Represents a single numeric value within a range
-   **JSON Viewer**: Formats and displays JSON data for readability
-   **Alive Status**: Indicates the active status of a broker topic
-   **Publisher**: Sends messages to a broker topic
-   **Logs**: Displays real-time log messages from broker topics
-   **Progress Bar**: Visual indicator of progress

## Usage

## Webpage

The webpage is the main entry point of the application. It is defined using the following syntax:

```
Webpage WebPageName
    author: "Author Name"
    version: "1.0.0"
    description: "Description of the webpage"
    navbar: true
```

-   **author**: The author of the webpage
-   **version**: The version of the webpage
-   **description**: A description of the webpage
-   **navbar**: If true, the webpage will have a navbar. This is optional and can be used to set a custom navbar for the webpage.

## Connections

Connections are the way to connect to a data source. They are defined using the following syntax:

-   For message brokers:

```
Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: ''
        password: ''
end

Broker<Redis> LocalRedis
    host: 'localhost'
    port: 6379
    db: 0
    auth:
        username: ''
        password: ''
end

Broker<AMQP> MyAMQPBroker
    host: 'localhost'
    port: 5672
    vhost: '/'
    auth:
        username: ''
        password: ''
end
```

-   **host**: Host IP address or hostname for the Broker
-   **port**: Broker Port number
-   **auth**: Authentication credentials. Unified for all communication brokers
    -   **username**: Username used for authentication
    -   **password**: Password used for authentication
-   **vhost (Optional)**: Vhost parameter. Only for AMQP brokers
-   **db (Optional)**: Database number parameter. Only for Redis brokers

**If at least one message broker is used, there must also be defined a websocket connection, that is used to connect the frontend with the backend. Only one websocket connection is needed for each application.**

```
Websocket MyWebsocket
    host: '0.0.0.0'
    port: 8000
end
```

-   **host**: Host IP address or hostname for the Websocket
-   **port**: Websocket Port number

-   For databases:

```
Database<MongoDB> HomeMongoDB
    host: 'localhost'
    port: 27017
    database: 'mydb'
    auth:
        username: ''
        password: ''
end

Database<MySQL> HomeMySQL
    host: 'localhost'
    port: 3306
    database: 'mydb'
    auth:
        username: ''
        password: ''
end
```

-   **host**: Host IP address or hostname for the database
-   **port**: Database Port number
-   **database**: Database name
-   **auth**: Authentication credentials. Unified for all databases

    -   **username**: Username used for authentication
    -   **password**: Password used for authentication

-   For REST APIs:

```
RestApi MyRestApi
    host: 'http://localhost'
    port: 8000
    headers: {"Authorization": "Bearer token"}
end
```

-   **host**: The url of the REST API
-   **port**: The port of the REST API
-   **headers**: Headers to be sent with the request. This is optional and can be used to send authentication tokens or other headers.

**If at least one REST API or database is used, there must also be defined an API connection, that is used to connect the frontend with the backend. Only one API connection is needed for each application.**

```
API MyAPI
    host: '0.0.0.0'
    port: 8000
end
```

-   **host**: Host IP address or hostname for the API
-   **port**: API Port number

**Authentication between the frontend and the backend is automatically handled by the DSL. The frontend will automatically send the authentication token to the backend, and the backend will automatically validate the token. This is done for both the Websocket and the API connections. Also, all the information of the connections are stored in the backend.**

## Data Sources

Data sources are the specific endpoints, queries or topics that are used to retrieve or send data. They are defined using the following syntax:

-   For message brokers:

```
BrokerTopic TopicName
    connection: <BrokerName>
    topic: 'my/topic'
end
```

-   **connection**: The name of the connection to the message broker
-   **topic**: The topic to subscribe or publish to

-   For databases:

```
MySQLQuery MyQueryName
    connection: <DatabaseName>
    query: 'SELECT * FROM mytable'
end

MongoDBQuery MyQueryName
    connection: <DatabaseName>
    collection: 'mycollection'
    filter: '{"field": "value"}'
end
```

-   **connection**: The name of the connection to the database
-   **query**: The SQL query to execute (for MySQL)
-   **collection**: The name of the collection to query (for MongoDB)
-   **filter**: The filter to apply to the query (optional for MongoDB)

-   For REST APIs:

```
RestEndpoint EndpointName
    connection: <RestApiName>
    path: '/api/v1/resource'
    method: 'POST'
    body: {"key": "value"}
    params: {"param1": "value1", "param2": "value2"}
```

-   **connection**: The name of the connection to the REST API
-   **path**: The path of the endpoint
-   **method**: The HTTP method to use (GET, POST, PUT, DELETE), if not specified, GET is used
-   **body**: The body of the request (for POST and PUT), optional
-   **params**: The query parameters to include in the request, optional

## Entities

Entities are used to define data models and their relationships with data sources. They are defined using the following syntax:

```
Entity EntityName
    description: 'Description of the entity'
    source: <DataSourceName>
    strict: true
    interval: 5000
    attributes:
        - attribute_name: attribute_type
end
```

-   **description**: A description of the entity,
-   **source**: The name of the data source to use
-   **strict**: When set to true, the entity only accepts data that matches its defined attributes exactly. Any undefined attributes will be rejected, and references to non-existent attributes will result in a validation error. When false, the entity can accept additional, undefined attributes without error.
-   **interval**: The interval in milliseconds for the entity to reload data from the data source. This is optional and can be used to set a custom interval for the entity in case of rest apis and databases.
-   **attributes**: A list of attributes for the entity. Each attribute has a name and a type.
-   **attribute_name**: The name of the attribute
-   **attribute_type**: The type of the attribute. The supported types are int, float, string, bool, list and dict.

### Entity Overloading

Entity overloading is a feature that allows you to a new entity that will replace an existing entity everywhere in the model. This is useful when you want to change the behavior of an entity without having to change all the references to it.

```
Entity NewEntityName overloads OldEntityName
    description: 'Description of the entity'
    source: <DataSourceName>
    strict: true
    interval: 5000
    attributes:
        - attribute_name: attribute_type
end
```

## Components

Components are used to define the visual representation of the data. They are defined using the following syntax:

```
Component ComponentName
    type: <ComponentType>
    entity: <EntityName>
end
```

-   **type**: The type of the component.
-   **entity**: The name of the entity to use. If not specified, the component should have static data.

After declaring a component you can use it in any screen by referencing it by its name.

```
use ComponentName
```

You can also declare a component inline in a screen. This is useful when you want to use a simple component only in one screen and not in the whole application.

### Component Types

There are many component types available in the DSL. They all have a common way to access the data from the entity. The data is accessed using the **accessors** that have this syntax: `this.attribute_name[array_index]...`
For example:

-   `this.temp[0]` will access the first element of the `temp` attribute of the entity.
-   `this.temp[0].value` will access the value of the first element of the `temp` attribute of the entity.
-   `this[0].data` will access the data of the first element of the entity.

For components that support static data, the syntax is different. The data is provided by strings or lists. More details on each component type.

Currently the DSL supports the following component types:

#### Text

```
Text
    content: <accessor> | "static text"
    size: 24
    color: "#fff"
    weight: "600"
```

-   **content**: The content of the text. It can be a string or an accessor.
-   **size**: The font size of the text.
-   **color**: The color of the text in hex string.
-   **weight**: The font weight of the text.

#### Image

```
Image
    source: <accessor> | "static image"
    width: 100
    height: 100
```

-   **source**: The source of the image. It can be a string or an accessor.
-   **width**: The width of the image.
-   **height**: The height of the image.

#### Bar Chart

```
BarChart
    description: "Description of the chart"
    xLabel: "Label for x axis"
    yLabel: "Label for y axis"
    xValue: <accessor> | "static x value"
    yValues: <accessor>, <accessor>... | "static y value", "static y value"...
    staticData: [ {...}, {...} ]
```

-   **description**: The description of the chart.
-   **xLabel**: The label for the x axis.
-   **yLabel**: The label for the y axis.
-   **xValue**: The x value of the chart. It can be a string or an accessor.
-   **yValues**: The y values of the chart. It can be strings or an accessors seperated by commas.
-   **staticData**: The static data of the chart. It can be a list of dictionaries.

#### Line Chart

```
LineChart
    description: "Description of the chart"
    xLabel: "Label for x axis"
    yLabel: "Label for y axis"
    xValue: <accessor> | "static x value"
    yValues: <accessor>, <accessor>... | "static y value", "static y value"...
    staticData: [ {...}, {...} ]
```

-   **description**: The description of the chart.
-   **xLabel**: The label for the x axis.
-   **yLabel**: The label for the y axis.
-   **xValue**: The x value of the chart. It can be a string or an accessor.
-   **yValues**: The y values of the chart. It can be strings or an accessors seperated by commas.
-   **staticData**: The static data of the chart. It can be a list of dictionaries.

#### Pie Chart

```
PieChart
    description: "Chart title or description"
    dataName: <accessor> | "static label key"
    value: <accessor> | "static value key"
    staticData: [ {...}, {...} ]
```

-   **description**: The description of the chart.
-   **dataName**: The key for each slice label, as accessor or static string.
-   **value**: The key for each slice value, as accessor or static string.
-   **staticData**: The static data of the chart. It can be a list of dictionaries.

#### Table

```
Table
    primary_key: "id"
    attributes: <accessor>, <accessor>, ...
    description: "Optional table description"
    table: "collection_or_table_name"
    crud: true
```

-   **primary_key**: The primary key of the table.
-   **attributes**: The data fields to display. It can be a list of accessors. Optional, if not specified, all attributes of the entity will be displayed.
-   **description**: The description of the table.
-   **table**: The name of the table or collection to use. Optional, for use with databases
-   **crud**: If true, the table will support CRUD operations. This is supported only for databases.

#### Live Table

```
LiveTable
    columns: <accessor>, <accessor>, ...
```

-   **columns**: The data fields to display. It can be a list of accessors. Optional, if not specified, all attributes of the entity will be displayed.

#### Form

```
Form
    description: "Form description"
    elements:
        Label "Your name"
        Input
            type: text
            placeholder: "Enter name"
            datakey: "username"
            required: true
```

-   **description**: The description of the form.
-   **elements**: The elements of the form. It can be a list of elements. Each element can be a label or input.
-   **Label**: The label of the element.
-   **Input**: The input of the element. It can be a text, number, email, password or checkbox.

#### Notification

```
Notification
    type: success | error | warning | info
    message: <accessor>
```

-   **type**: The type of the notification. It can be success, error, warning or info.
-   **message**: The message of the notification. It can be an accessor.

#### Gauge

```
Gauge
    value: <accessor> | 0.5
    description: "Battery level"
```

-   **value**: The value of the gauge. It can be an accessor or a static value.
-   **description**: The description of the gauge.

#### JSON Viewer

```
JsonViewer
    attributes: <accessor>, <accessor>, ...
```

-   **attributes**: The keys to display. It can be a list of accessors. Optional, if not specified, all attributes of the entity will be displayed.

#### Alive Status

```
Alive
    timeout: 5000
    description: "Sensor alive status"
```

-   **timeout**: The timeout in milliseconds. If the data source does not send data for this time, it will be considered dead.
-   **description**: The description of the alive status.

#### Publisher

```
Publish
    broker: <broker_ref>
    endpoint: <endpoint_ref>
    topic: "topic/name"
    json: '{"command": "start"}'
    description: "Send start signal"
```

-   **broker**: The name of the broker to use.
-   **endpoint**: The name of the endpoint to use.
    Either the broker or the endpoint is required.
-   **topic**: The topic to publish to. If not specified, the publisher will have an input field to enter the topic.
-   **json**: The JSON payload to send. If not specified, the publisher will have an input field to enter the payload.
-   **description**: The description of the publisher.

#### Logs

```
Logs
    attributes: <accessor>, <accessor>, ...

```

-   **attributes**: The keys to display. It can be a list of accessors. Optional, if not specified, all attributes of the entity will be displayed.

#### Progress Bar

```
Progressbar
    value: <accessor> | 0.4
    max: <accessor> | 100
    description: "Loading progress"
    barColor: "#00FF00"
    textColor: "#000000"
    trackColor: "#CCCCCC"
```

-   **value**: The value of the progress bar. It can be an accessor or a static value.
-   **max**: The maximum value of the progress bar. It can be an accessor or a static value.
-   **description**: The description of the progress bar.
-   **barColor**: The color of the progress bar. It can be a hex string.
-   **textColor**: The color of the text. It can be a hex string.
-   **trackColor**: The color of the track. It can be a hex string.

## Conditions

Conditions are very similar to conditions in imperative programming languages
such as Python, Java, C++ or JavaScript. You can use Entity Attributes in a
condition just like a variable by referencing it in the Condition using
it's Fully-Qualified Name (FQN) in dot (.) notation. They are used to dynamically show or hide components based on the data received from the data sources.

### Condition Formatting:

You can combine two conditions into a more complex one using logical operators but make sure to not forget the parenthesis.

The supported logical operators are:

-   **AND**: Logical AND
-   **OR**: Logical OR

### Condition Examples

Given that we have an entity named `TempSensor1` with attributes `temp`, `humidity` and components named `MyComponent`, `MyOtherComponent` we can use the following conditions:

```
if TempSensor1.temp > 10 and TempSensor1.humidity < 20
    use MyComponent, MyOtherComponent

if 0 > TempSensor1.temp > 10 or TempSensor1.humidity < 20
    use MyComponent
else
    use MyComponent, MyOtherComponent

if TempSensor1.temp > 10
    use MyComponent
else if TempSensor1.temp < 10
    use MyOtherComponent
else
    use MyComponent
```

The supported comparison operators are:

-   **>**: Greater than
-   **<**: Less than
-   **>=**: Greater than or equal to
-   **<=**: Less than or equal to
-   **==**: Equal to
-   **!=**: Not equal to

## Loops

Loops are used to iterate over a list of elements coming from the live data source. They are used to dynamically show or hide components based on the data received from the data sources. Loops currently support only the Text, Image and Gauge components.

### Loop Formatting:

You can use the following syntax to define a loop:

```
for item in <entity_name>.<attribute_name>
    use Text with item.value
    orientation: column
```

-   **orientation**: The orientation of the loop. It can be column or row.
-   **with**: The data accessor to use with the item. It needs to start with `item` and follows the accessor logic. If not specified, the component should have static data.

There can also be if statements inside the loop to show only a part of the data based on a condition. This condition is simpler than the one used in the conditions section. You can use the following syntax to define a condition inside a loop:

```
for item in CarData.metrics
    use Gauge with item.value if item.value > 30
    else use Text content:"Low Value"
    orientation: column
```

## Screens

Screens are used to define the layout of the application. They are defined using the following syntax:

```
Screen ScreenName
    description: "Description of the screen"
    title: "Title of the screen"
    url: "/home"


end
```

-   **description**: The description of the screen.
-   **title**: The title of the screen also used in the navbar.
-   **url**: The url of the screen. This is used to navigate to the screen.

Each screen can contain rows and columns to define the layout, links to other screens or external urls, components, conditions and loops.
The syntax for defining a row is:

```
row
endrow

```

The syntax for defining a column is:

```
col
endcol
```

The syntax for defining a link is:

```
link
    url: "/home"
    text: "Home"
end
```

The syntax for using a component is:

```
use ComponentName
```

or you can define it inline.

A complete example of a screen is:

```
Screen Home
    description: "Home screen"
    title: "Home"
    url: "/home"
    row
        col
            use MyComponent1
        endcol
        col
            Component Title
                type: Text content: "Hello World"
            end
        endcol
    endrow
end
```

## Import

The language supports multi-file models via model imports.
A nested model import layer is implemented, enabling pythonic imports
of models defined in other files.

```
// webpage.wdsl

import "screens.wdsl"

Webpage MyWebpage
    author: ""
    version: "1.0"
    description: ""
    navbar: true

    API backendAPI
        host: "0.0.0.0"
        port: 8321
    end

    Websocket backendWebsocket
        host: "localhost"
        port: 8080
    end
```

```
// screens.wdsl
import "components.wdsl"

Screen Home
    title: "Home"
    url: "/"

    use InfoNotifications

    row
        col
            use ProductsTable
        endcol
        col
            use WarehousesTable
        endcol
    endrow
end
```

The model can be seperated into as many files as needed.

## Validation <a name="validation"></a>

Validation is perfomed using either the CLI or the REST API of the DSL.

In the case of the CLI, `validate` is a subcommand of `webdsl`.

To validate a WebDSL model file, execute:

```bash
webdsl validate <webdsl_file>
```

If the model passes the validation rules (grammar) you should see something
like:

```bash
✔ Model is valid.
```

## Code Generation <a name="generation"></a>

Code generation is perfomed using either the CLI or the REST API of the DSL.

In the case of the CLI, `generate` is a subcommand of `webdsl`.

To generate the source code of a WebDSL model, execute:

```bash
webdsl generate <webdsl_file> <output_dir>
```

The generated code will be placed in the specified output directory. If no output dir is provided, the code will be generated in the current directory.

## OpenAPI Transformations <a name="openapi"></a>

WebDSL also supports transforming OpenAPI specifications into WebDSL models using the openapi subcommand of the webdsl CLI tool. This transformation automatically generates the necessary components, entities, and data sources based on the provided OpenAPI specification. The resulting model can then be used to generate the full application source code.

By default, the transformation extracts the API connection details and creates a separate data source for each endpoint defined in the OpenAPI spec.

### Augmenting OpenAPI with WebDSL

WebDSL allows you to enhance the OpenAPI specification by using a custom header on specific endpoints. You can add the following annotation to generate UI components:

```yaml
x-webdsl:
    - this.id -> Gauge @ 1,1
    - this[0].title -> Text @ 1,2
```

In this example:

A Gauge component will be generated from the id field of the response.

A Text component will be generated from the title field of the first item in the response array.

The @ 1,1 and @ 1,2 specify the row and column positions of the components (1-indexed).

To transform an OpenAPI specification into a WebDSL model, execute:

```bash
webdsl openapi <openapi_file> <output_dir>
```

If the OpenAPI file is valid, the generated WebDSL model will be placed in the specified output directory. If no output dir is provided, the code will be generated in the current directory.

## GoalDSL Transformations <a name="goal-dsl"></a>

WebDSL also supports transforming [GoalDSL](https://github.com/robotics-4-all/goal-dsl) into WebDSL models. This is currently only supported on the REST API of WebDSL and not on the CLI.

## Examples <a name="examples"></a>

Several examples of usage can be found under the [examples directory](./web_dsl/examples/) of this repository.
