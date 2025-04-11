import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { IoReload } from "react-icons/io5";

const Text = ({
    topic,
    attribute,
    size = 18,
    color,
    sourceOfContent,
    restData,
    staticContent
}) => {
    const [content, setContent] = useState("");
    const ws = useContext(WebsocketContext);

    const fetchValue = () => {
        const { host, port, path, method, headers, params } = restData;

        proxyRestCall({
            host,
            port,
            path,
            method: "GET",
            headers,
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

    useEffect(() => {
        if (sourceOfContent === "rest") {
            fetchValue();
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
    return (
        <div className="flex relative w-fit h-fit p-5">
            {"rest" === sourceOfContent && (
                <button
                    className="absolute top-0 right-0 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={fetchValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {sourceOfContent === "rest" || sourceOfContent === "broker" ? (
                <h1 style={{ fontSize: `${size}px`, color: `${color}` }}>
                    {content}
                </h1>
            ) : (
                <h1 style={{ fontSize: `${size}px`, color: `${color}` }}>
                    {staticContent}
                </h1>
            )}
        </div>
    );
};

export default Text;
