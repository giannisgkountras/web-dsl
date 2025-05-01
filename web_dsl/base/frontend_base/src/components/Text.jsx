import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { IoReload } from "react-icons/io5";
import { getValueByPath } from "../utils/getValueByPath";
import { evaluateCondition } from "../utils/evaluateCondition";

const Text = ({
    topic,
    contentPath,
    size = 18,
    color,
    sourceOfContent,
    restData,
    staticContent,
    dbData,
    condition = true
}) => {
    const [content, setContent] = useState("");
    const [componentVisible, setComponentVisible] = useState(true);

    const ws = useContext(WebsocketContext);

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            fetchValueFromRest(restData, contentPath, setContent);
        }
        if (sourceOfContent === "db") {
            fetchValueFromDB(dbData, contentPath, setContent);
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setContent(getValueByPath(msg, contentPath));
            setComponentVisible(evaluateCondition(condition, msg));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    return (
        componentVisible && (
            <div className="flex relative w-fit h-fit p-5">
                {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                    <button
                        className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
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
        )
    );
};

export default Text;
