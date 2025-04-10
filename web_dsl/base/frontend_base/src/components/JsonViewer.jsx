import React, { useState, useEffect, useContext } from "react";
import JsonView from "@uiw/react-json-view";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import customTheme from "../utils/jsonviewtheme";
import { toast } from "react-toastify";
import { IoReload } from "react-icons/io5";
import { proxyRestCall } from "../api/proxyRestCall";

const JsonViewer = ({ topic, attributes, sourceOfContent, restData }) => {
    const [jsonData, setJsonData] = useState({});
    const ws = useContext(WebsocketContext);

    const fetchValue = () => {
        const { host, port, path, method, headers, params } = restData;

        proxyRestCall({
            host,
            port,
            path,
            method,
            headers,
            params
        })
            .then((response) => {
                try {
                    if (attributes.length === 0) {
                        // If no attributes are provided, set the entire message as JSON data
                        try {
                            setJsonData(response);
                        } catch (error) {
                            toast.error(
                                "An error occurred while updating value: " +
                                    error.message
                            );
                            console.error("Error updating status:", error);
                        }
                    } else {
                        const newJsonData = {};
                        attributes.forEach((attribute) => {
                            try {
                                newJsonData[attribute.name] = convertTypeValue(
                                    response[attribute.name],
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
                } catch (error) {
                    toast.error(
                        "An error occurred while converting value: " +
                            error.message
                    );
                }
            })
            .catch((error) => {
                toast.error("Error fetching initial value: " + error.message);
                console.error("Error fetching initial value:", error);
            });
    };

    useEffect(() => {
        if (sourceOfContent === "rest") {
            fetchValue();
        }
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
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
        <div className="flex justify-center flex-col items-center p-4 w-fit bg-[#111828] rounded-2xl relative">
            {"broker" === sourceOfContent && (
                <h1 className="mb-2 text-lg font-semibold text-gray-200">
                    Watching <span className="text-pink-400">{topic}</span>
                </h1>
            )}
            {"rest" === sourceOfContent && (
                <button
                    className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer z-10"
                    onClick={fetchValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            <JsonView value={jsonData} style={customTheme} />
        </div>
    );
};

export default JsonViewer;
