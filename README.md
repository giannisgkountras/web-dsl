# Textual DSL for web applications
<image src="https://github.com/user-attachments/assets/66af57d6-f84b-416a-924a-5fa0a64e7600" alt="web-dsl" width="500px"/>

## How to setup

### Pre-requisites

-   Docker

### Steps

1. Clone the repository
2. Run `docker compose up --build`
3. Access the application at `http://localhost:8082`

## Components

### Notification Component

-   Displays a notification message to the user
-   Expects a message from the broker `{data: "Message to display"}`
-   Has types `success`, `info`, `warning`, `error`

### Line Chart Component

-   Displays a line chart with the data received from the broker
-   Expects a message from the broker `{data: { x_axis: 1, y_axis: 10 }}`
-   Has options to customize the chart with axis labels and data keys
