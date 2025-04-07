import { toast } from "react-toastify";
import { WebsocketContext } from "../context/WebsocketContext";
import { useContext, useState, useEffect, use } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import convertTypeValue from "../utils/convertTypeValue";

const LiveNotification = ({ type = "info", topic, attribute }) => {
    const ws = useContext(WebsocketContext);
    const [message, setMessage] = useState("");

    const notify = {
        success: () => toast.success(message),
        error: () => toast.error(message),
        info: () => toast.info(message),
        warning: () => toast.warning(message)
    };

    useWebsocket(ws, topic, (msg) => {
        try {
            setMessage(convertTypeValue(msg[attribute.name], attribute.type));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    useEffect(() => {
        if (message !== "") {
            notify[type]();
        }
    }, [message]);
};

export default LiveNotification;
