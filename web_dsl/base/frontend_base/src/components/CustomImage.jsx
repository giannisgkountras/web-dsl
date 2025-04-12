import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import placeholder from "../assets/placeholderimage";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { IoReload } from "react-icons/io5";

const CustomImage = ({
    topic,
    width,
    height,
    source,
    sourceOfContent,
    restData,
    sourceStatic
}) => {
    const ws = useContext(WebsocketContext);
    const [frame, setFrame] = useState(placeholder);

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
                    const newFrame = `data:image/png;base64,${convertTypeValue(
                        response[source.name],
                        source.type
                    )}`;
                    setFrame(newFrame);
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
            setFrame(
                `data:image/png;base64,${convertTypeValue(
                    msg[source.name],
                    source.type
                )}`
            );
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return (
        <div className="w-fit h-fit relative">
            {"rest" === sourceOfContent && (
                <button
                    className="absolute top-0 right-0 p-4 z-10 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={fetchValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {sourceOfContent === "rest" || sourceOfContent === "broker" ? (
                <img
                    style={{
                        width: `${width ? width : 400}px`,
                        height: `${height ? height : 400}px`
                    }}
                    src={frame}
                ></img>
            ) : (
                <img
                    style={{
                        width: `${width ? width : 400}px`,
                        height: `${height ? height : 400}px`
                    }}
                    src={sourceStatic}
                ></img>
            )}
        </div>
    );
};

export default CustomImage;
