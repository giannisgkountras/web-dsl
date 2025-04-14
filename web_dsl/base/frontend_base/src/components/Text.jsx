import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { IoReload } from "react-icons/io5";

const Text = ({
    topic,
    attribute,
    size = 18,
    color,
    sourceOfContent,
    restData,
    staticContent,
    dbData
}) => {
    const [content, setContent] = useState("");
    const ws = useContext(WebsocketContext);
    const fetchValue = () => {
        const { name, path, method, params } = restData;

        proxyRestCall({
            name,
            path,
            method: "GET",
            params
        })
            .then((response) => {
                try {
                    const newContent = convertTypeValue(
                        response[attribute.name],
                        attribute.type
                    );
                    setContent(newContent);
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

    const fetchFromDB = () => {
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
                    // check if response is a list
                    let responseRow = null;
                    if (Array.isArray(response)) {
                        responseRow = response[0];
                    } else {
                        responseRow = response;
                    }

                    const value = convertTypeValue(
                        responseRow[attribute.name],
                        attribute.type
                    );
                    setContent(value);
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
        if (sourceOfContent === "db") {
            fetchFromDB();
        }
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

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            fetchValue();
        }
        if (sourceOfContent === "db") {
            fetchFromDB();
        }
    };

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
