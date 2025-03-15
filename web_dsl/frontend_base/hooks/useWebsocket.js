// Custom hook that listens for incoming WebSocket messages
import { useEffect } from "react";

export const useWebsocket = (ws, topic, onMessageCallback) => {
    useEffect(() => {
        if (!ws) {
            return;
        }

        ws.onmessage = (messageEvent) => {
            const messageData = JSON.parse(messageEvent.data);

            if (messageData[topic] !== undefined) {
                onMessageCallback(messageData[topic]);
            } else {
                return;
            }
        };
    }, [ws, topic, onMessageCallback]);

    return ws;
};
