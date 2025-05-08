import { toast } from "react-toastify";
import { WebsocketContext } from "../context/WebsocketContext";
import { useContext, useState, useEffect, use } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { getValueByPath } from "../utils/getValueByPath";

const LiveNotification = ({ type = "info", topic, contentPath }) => {
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
            setMessage(getValueByPath(msg, contentPath));
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
