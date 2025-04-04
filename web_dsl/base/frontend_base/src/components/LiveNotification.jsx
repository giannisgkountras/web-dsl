import { toast } from "react-toastify";
import { WebsocketContext } from "../context/WebsocketContext";
import { useContext, useState, useEffect, use } from "react";
import { useWebsocket } from "../hooks/useWebsocket";

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
        setMessage(msg[attribute.name]);
    });

    useEffect(() => {
        if (message !== "") {
            notify[type]();
        }
    }, [message]);
};

export default LiveNotification;
