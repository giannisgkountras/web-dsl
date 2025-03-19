# Textual DSL for web applications

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

### Line Chart Component

-   Displays a line chart with the data received from the broker
-   Expects a message from the broker `{data: { x_axis: 1, y_axis: 10 }}`
