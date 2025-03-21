# Textual DSL for web applications
<image src="https://private-user-images.githubusercontent.com/110430201/425225947-5d2d711c-e401-488f-9d49-25715116a87b.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDI1Njc3MzMsIm5iZiI6MTc0MjU2NzQzMywicGF0aCI6Ii8xMTA0MzAyMDEvNDI1MjI1OTQ3LTVkMmQ3MTFjLWU0MDEtNDg4Zi05ZDQ5LTI1NzE1MTE2YTg3Yi5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMzIxJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDMyMVQxNDMwMzNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT02MzYzOTVmMDI2ZWZlYjEyZWJhODBjNmMyMjY1NDgxMzYyODJlMjlkZWQzMWZkMDVmODA5MDQ4Y2UxOWRhNjE0JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.GCCygUZf_OY5nU2w7DFCHYPunedM0RC63vYpxeBBEn0" alt="web-dsl" width="500px"/>
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
