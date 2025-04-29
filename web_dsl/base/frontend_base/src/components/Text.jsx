import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { IoReload } from "react-icons/io5";

const Text = ({
    topic,
    attribute,
    size = 18,
    color,
    sourceOfContent,
    restData,
    staticContent,
    dbData,
    contentPath
}) => {
    const [content, setContent] = useState("");
    // const setContentGeneral = (value) => {
    //     if (indexedAttribute) {
    //         setContent(value[indexedAttribute.index][indexedAttribute.name]);
    //     } else {
    //         setContent(value);
    //     }
    // };
    const ws = useContext(WebsocketContext);

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            fetchValueFromRest(restData, attribute, setContent);
        }
        if (sourceOfContent === "db") {
            fetchValueFromDB(dbData, attribute, setContent);
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setContent(convertTypeValue(msg[attribute.name], attribute.type));
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
                    className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={reloadContent}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {sourceOfContent === "static" ? (
                <h1 style={{ fontSize: `${size}px`, color: `${color}` }}>
                    {staticContent}
                </h1>
            ) : (
                <h1 style={{ fontSize: `${size}px`, color: `${color}` }}>
                    {content}
                </h1>
            )}
        </div>
    );
};

export default Text;
