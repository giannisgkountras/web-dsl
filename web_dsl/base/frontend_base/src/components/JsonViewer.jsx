import { useState, useEffect, useContext } from "react";
import JsonView from "@uiw/react-json-view";
import { WebsocketContext } from "../context/WebsocketContext";
import customTheme from "../utils/jsonviewtheme";
import { toast } from "react-toastify";
import { IoReload } from "react-icons/io5";
import { getNameFromPath, getValueByPath } from "../utils/getValueByPath";

const JsonViewer = ({
    entityData,
    topic,
    attributes = [],
    sourceOfContent
}) => {
    const [jsonData, setJsonData] = useState({});

    useEffect(() => {
        try {
            if (attributes.length === 0) {
                // If no attributes are provided, set the entire message as JSON data
                setJsonData(entityData);
            } else {
                const newJsonData = {};
                attributes.forEach((attribute) => {
                    const value = getValueByPath(entityData, attribute);
                    const name = getNameFromPath(attribute);
                    newJsonData[name] = value;
                });
                setJsonData(newJsonData);
            }
        } catch (error) {
            toast.error(
                "An error occurred while converting value: " + error.message
            );
        }
    }, [entityData]);

    return (
        <div className="flex justify-center flex-col items-center p-4 w-fit bg-[#111828] rounded-2xl relative">
            {"broker" === sourceOfContent && (
                <h1 className="mb-2 text-lg font-semibold text-gray-200">
                    Watching <span className="text-pink-400">{topic}</span>
                </h1>
            )}

            {jsonData && <JsonView value={jsonData} style={customTheme} />}
            {!jsonData && (
                <div className="flex justify-center items-center w-full h-64 text-white">
                    <p className="animate-pulse">Loading data...</p>
                </div>
            )}
        </div>
    );
};

export default JsonViewer;
