import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { IoReload } from "react-icons/io5";
import { getValueByPath } from "../utils/getValueByPath";
import {
    evaluateCondition,
    evaluateConditionWithData
} from "../utils/evaluateCondition";

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
            const data = fetchValueFromRest(restData, contentPath);
            setComponentVisible(evaluateConditionWithData(condition, data));
            setContent(data);
        }
        if (sourceOfContent === "db") {
            const data = fetchValueFromDB(dbData, contentPath);
            setComponentVisible(evaluateConditionWithData(condition, data));
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
            setComponentVisible(evaluateConditionWithData(condition, data));
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
