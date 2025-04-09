import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { toast } from "react-toastify";

const Text = ({ topic, attribute }) => {
    const [content, setContent] = useState("");
    const ws = useContext(WebsocketContext);

    useWebsocket(ws, topic, (msg) => {
        try {
            setContent(convertTypeValue(msg[attribute.name], attribute.type));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return <h1>{content}</h1>;
};

export default Text;
