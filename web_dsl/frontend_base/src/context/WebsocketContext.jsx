import { createContext, useEffect, useState } from "react";

// Create a context for the WebSocket
export const WebsocketContext = createContext(null);

// Provider component to establish and provide the WebSocket connection
export const WebsocketProvider = ({ children }) => {
    const [ws, setWs] = useState(null);
    const host = "localhost";
    const port = 8765;

    useEffect(() => {
        const websocket = new WebSocket(`ws://${host}:${port}`);

        websocket.onopen = () => {
            console.log("WebSocket is connected");
        };

        websocket.onclose = () => {
            console.log("WebSocket is closed");
        };

        setWs(websocket);
        // Clean up the connection when the component unmounts
        return () => {
            websocket.close();
        };
    }, []);

    return (
        <WebsocketContext.Provider value={ws}>
            {children}
        </WebsocketContext.Provider>
    );
};
