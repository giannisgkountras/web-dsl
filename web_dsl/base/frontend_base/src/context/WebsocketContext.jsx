import { createContext, useEffect, useState, useRef } from "react"; // Import useState
import { toast } from "react-toastify";
import config from "./websocketConfig.json";
import { useAuth } from "./AuthContext";

export const WebsocketContext = createContext(null);

export const WebsocketProvider = ({ children }) => {
    const { ws_token, isLoading } = useAuth();
    // *** Use useState for the connection object to trigger re-renders in children ***
    const [ws, setWs] = useState(null);
    const retryCountRef = useRef(0);
    const maxRetries = 5;
    const baseDelay = 5000;
    const isClosing = useRef(false);

    useEffect(() => {
        if (isLoading) {
            return;
        }

        isClosing.current = false;

        const connectWebSocket = () => {
            if (retryCountRef.current >= maxRetries) {
                toast.error("Error connecting to WebSocket!");
                return;
            }
            let websocket
            if (config?.secure === "enabled") {
                console.log("Using secure WebSocket connection (wss)...");
                websocket = new WebSocket(`wss://${config.host}:${config.port}`);
            } else {
                console.log("Using insecure WebSocket connection (ws)...");
                websocket = new WebSocket(`ws://${config.host}:${config.port}`);
            }

            websocket.onopen = () => {
                console.log("WebSocket is connected, updating context...");
                websocket.send(ws_token);
                toast.success("WebSocket is connected!");
                retryCountRef.current = 0;
                setWs(websocket);
            };

            websocket.onclose = () => {
                if (isClosing.current) {
                    console.log("Connection closed intentionally.");
                    return;
                }
                setWs(null); // Set ws to null on disconnect
                if (retryCountRef.current < maxRetries) {
                    retryCountRef.current += 1;
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

        return () => {
            isClosing.current = true;
            if (ws) {
                ws.close();
            }
        };
        // This effect's job is to establish the connection once, based on the token.
    }, [ws_token, isLoading]);

    // Provide the state variable to the context
    return <WebsocketContext.Provider value={ws}>{children}</WebsocketContext.Provider>;
};
