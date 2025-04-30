import React, { useState, useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import placeholder from "../assets/placeholderimage";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { IoReload } from "react-icons/io5";
import { getValueByPath } from "../utils/getValueByPath";

const CustomImage = ({
    topic,
    width,
    height,
    source,
    sourceOfContent,
    restData,
    sourceStatic,
    contentPath
}) => {
    const ws = useContext(WebsocketContext);
    const [frame, setFrame] = useState(placeholder);

    const reloadContent = () => {
        if (sourceOfContent === "rest") {
            fetchValueFromRest(restData, contentPath, setFrame);
        }
        if (sourceOfContent === "db") {
            fetchValueFromDB(dbData, contentPath, setFrame);
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setFrame(
                `data:image/png;base64,${getValueByPath(msg, contentPath)}`
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
