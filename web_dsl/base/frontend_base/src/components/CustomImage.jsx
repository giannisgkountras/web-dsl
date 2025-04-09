import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import placeholder from "../assets/placeholderimage";
import { toast } from "react-toastify";

const CustomImage = ({ topic, width, height, source }) => {
    const ws = useContext(WebsocketContext);
    const [frame, setFrame] = useState(placeholder);

    useWebsocket(ws, topic, (msg) => {
        try {
            setFrame(convertTypeValue(msg[source.name], source.type));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return (
        <img
            style={{
                width: `${width}px`,
                height: `${height}px`
            }}
            src={`data:image/png;base64,${frame}`}
        ></img>
    );
};

export default CustomImage;
