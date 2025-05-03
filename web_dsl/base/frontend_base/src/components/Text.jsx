import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { IoReload } from "react-icons/io5";
import { getValueByPath } from "../utils/getValueByPath";

const Text = ({
    topic,
    contentPath,
    size = 18,
    color,
    sourceOfContent,
    restData,
    staticContent,
    dbData
}) => {
    const [content, setContent] = useState("");

    const ws = useContext(WebsocketContext);

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            const data = fetchValueFromRest(restData, contentPath);
            setContent(data);
        }
        if (sourceOfContent === "db") {
            const data = fetchValueFromDB(dbData, contentPath);
            setContent(data);
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const data = getValueByPath(msg, contentPath);
            setContent(data);
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    return (
        <div className="flex relative w-fit h-fit p-5">
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    className="absolute top-[-5] right-[-25] p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={reloadContent}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}

            <h1
                style={{
                    ...(size !== 0 && { fontSize: `${size}px` }),
                    color: color
                }}
            >
                {sourceOfContent === "static" ? staticContent : content}
            </h1>
        </div>
    );
};

export default Text;
