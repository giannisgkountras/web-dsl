import React, { useState, useContext } from "react";
import JsonView from "@uiw/react-json-view";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import customTheme from "../utils/jsonviewtheme";
import { toast } from "react-toastify";

const JsonViewer = ({ topic, attributes = [] }) => {
    const [jsonData, setJsonData] = React.useState({});
    const ws = useContext(WebsocketContext);

    useWebsocket(ws, topic, (msg) => {
        if (attributes.length === 0) {
            // If no attributes are provided, set the entire message as JSON data
            try {
                setJsonData(msg);
            } catch (error) {
                toast.error(
                    "An error occurred while updating value: " + error.message
                );
                console.error("Error updating status:", error);
            }
        } else {
            const newJsonData = {};
            attributes.forEach((attribute) => {
                try {
                    newJsonData[attribute.name] = convertTypeValue(
                        msg[attribute.name],
                        attribute.type
                    );
                } catch (error) {
                    toast.error(
                        "An error occurred while updating value: " +
                            error.message
                    );
                    console.error("Error updating status:", error);
                }
            });
            setJsonData(newJsonData);
        }
    });
    return (
        <div className="flex justify-center flex-col items-center p-4 w-fit bg-[#111828] rounded-2xl">
            <h1 className="mb-2 text-lg font-semibold text-gray-200">
                Watching <span className="text-pink-400">{topic}</span>
            </h1>
            <JsonView value={jsonData} style={customTheme} />
        </div>
    );
};

export default JsonViewer;
