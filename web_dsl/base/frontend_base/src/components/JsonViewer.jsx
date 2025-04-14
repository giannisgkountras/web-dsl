import React, { useState, useEffect, useContext } from "react";
import JsonView from "@uiw/react-json-view";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import customTheme from "../utils/jsonviewtheme";
import { toast } from "react-toastify";
import { IoReload } from "react-icons/io5";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";

const JsonViewer = ({
    topic,
    attributes,
    sourceOfContent,
    restData,
    dbData
}) => {
    const [jsonData, setJsonData] = useState({});
    const ws = useContext(WebsocketContext);

    const fetchValue = () => {
        const { name, path, method, params } = restData;

        proxyRestCall({
            name,
            path,
            method,
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

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            fetchValue();
        }
        if (sourceOfContent === "db") {
            fetchDB();
        }
    };
    useEffect(() => {
        reloadContent();
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

    const fetchDB = () => {
        const { connection_name, database, query, collection, filter } = dbData;
        queryDB({
            connection_name,
            database,
            query,
            collection,
            filter
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
                        const responseRow = Array.isArray(response)
                            ? response[0]
                            : response;
                        attributes.forEach((attribute) => {
                            try {
                                newJsonData[attribute.name] = convertTypeValue(
                                    responseRow[attribute.name],
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
                    onClick={reloadContent}
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
