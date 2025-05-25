import { createContext, useEffect, useRef, useState } from "react";
import { toast } from "react-toastify";
import config from "./websocketConfig.json";

// Create a context for the WebSocket
export const WebsocketContext = createContext(null);

// Provider component to establish and provide the WebSocket connection
export const WebsocketProvider = ({ children }) => {
    const SECRET_KEY = import.meta.env.VITE_SECRET_KEY;
    const [ws, setWs] = useState(null);
    const retryCountRef = useRef(0); // Use useRef to persist retry count across re-renders
    const maxRetries = 5; // Max retry attempts
    const baseDelay = 5000; // 5 second delay between attempts

    const connectWebSocket = () => {
        if (retryCountRef.current >= maxRetries) {
            console.log("Max retries reached. Stopping reconnection attempts.");
            toast.error("Error connecting to WebSocket!");
            return;
        }

        console.log(
            `Attempting WebSocket connection... (Attempt ${
                retryCountRef.current + 1
            })`
        );

        const websocket = new WebSocket(`ws://${config.host}:${config.port}`);

        websocket.onopen = () => {
            console.log("WebSocket is connected");
            toast.success("WebSocket is connected!");
            retryCountRef.current = 0; // Reset retry count on successful connection

            // Send the secret key immediately after connection is established.
            if (SECRET_KEY) {
                console.log("Sending secret key for authentication...");
                websocket.send(SECRET_KEY);
            } else {
                console.warn(
                    "No secret key configured to send over WebSocket."
                );
            }
        };

        websocket.onclose = () => {
            console.log("WebSocket is closed.");
            if (retryCountRef.current < maxRetries) {
                retryCountRef.current += 1;

                console.log(`Reconnecting in ${baseDelay / 1000} seconds...`);
                toast.warn("Reconnecting to WebSocket...");
                setTimeout(connectWebSocket, baseDelay);
            }
        };

        websocket.onerror = (error) => {
            console.log("WebSocket error:", error);
            websocket.close(); // Ensure the connection is properly closed before retrying
        };

        setWs(websocket);
    };

    useEffect(() => {
        connectWebSocket();

        return () => {
            if (ws) ws.close();
        };
    }, []);

    return (
        <WebsocketContext.Provider value={ws}>
            {children}
        </WebsocketContext.Provider>
    );
};
