import { createContext, useEffect, useRef } from "react";
import { toast } from "react-toastify";
import config from "./websocketConfig.json";
import { useAuth } from "./AuthContext";

export const WebsocketContext = createContext(null);

export const WebsocketProvider = ({ children }) => {
    // Get both ws_token and isLoading from the AuthContext
    const { ws_token, isLoading } = useAuth();
    const ws = useRef(null);
    const retryCountRef = useRef(0);
    const maxRetries = 5;
    const baseDelay = 5000;

    useEffect(() => {
        // Do not attempt to connect if auth is loading or if there is no token.
        if (isLoading || !ws_token) {
            return;
        }

        const connectWebSocket = () => {
            if (retryCountRef.current >= maxRetries) {
                console.log("Max retries reached. Stopping reconnection attempts.");
                toast.error("Error connecting to WebSocket!");
                return;
            }

            console.log(`Attempting WebSocket connection... (Attempt ${retryCountRef.current + 1})`);

            const websocket = new WebSocket(`ws://${config.host}:${config.port}`);
            ws.current = websocket;

            websocket.onopen = () => {
                console.log("Sending secret key for authentication...");
                websocket.send(ws_token);
                console.log("WebSocket is connected");
                toast.success("WebSocket is connected!");
                retryCountRef.current = 0;
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
                websocket.close();
            };
        };

        connectWebSocket();

        // Cleanup function to close the WebSocket connection when the component unmounts
        // or when the dependencies (isLoading, ws_token) change.
        return () => {
            if (ws.current) {
                console.log("Closing WebSocket connection.");
                ws.current.close();
            }
        };
    }, [ws_token, isLoading]);

    return <WebsocketContext.Provider value={ws.current}>{children}</WebsocketContext.Provider>;
};
