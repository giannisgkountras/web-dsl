// Custom hook that listens for incoming WebSocket messages
import { useEffect } from "react";

export const useWebsocket = (ws, topic, onMessageCallback) => {
    useEffect(() => {
        if (!ws) return;

        const messageHandler = (messageEvent) => {
            const messageData = JSON.parse(messageEvent.data);
            if (messageData[topic] !== undefined) {
                onMessageCallback(messageData[topic]);
            }
        };

        ws.addEventListener("message", messageHandler);

        // Cleanup: remove the event listener on unmount or dependency change
        return () => {
            ws.removeEventListener("message", messageHandler);
        };
    }, [ws, topic, onMessageCallback]);

    return ws;
};
