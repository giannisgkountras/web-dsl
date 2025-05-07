import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { useEffect } from "react";
import { IoReload } from "react-icons/io5";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { getValueByPath } from "../utils/getValueByPath";

const ProgressBar = ({
    topic,
    sourceOfContent,
    restData,
    staticValue,
    dbData,
    contentPath,
    max = 100,
    description,
    barColor = "#80A499",
    textColor = "#fff",
    trackColor = "#3c544c"
}) => {
    const ws = useContext(WebsocketContext);
    const [currentValue, setCurrentValue] = useState(staticValue || 0);
    const percentage = Math.min((currentValue / max) * 100, 100);
    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const data = getValueByPath(msg, contentPath);
            setCurrentValue(data);
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    const reloadValue = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRest(restData, contentPath);
            setCurrentValue(data);
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDB(dbData, contentPath);
            setCurrentValue(data);
        }
    };

    useEffect(() => {
        reloadValue();
    }, []);
    return (
        <div className="w-full flex flex-col justify-center items-center relative">
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    className="absolute top-0 right-[25] text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={reloadValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            <div className="w-2/3">
                {description && (
                    <div className="mb-1 text-sm font-medium">
                        {description}
                    </div>
                )}
                <div
                    className="w-full rounded-full h-4 overflow-hidden"
                    style={{ backgroundColor: trackColor }}
                >
                    <div
                        className="h-full transition-all duration-500"
                        style={{
                            width: `${percentage}%`,
                            backgroundColor: barColor
                        }}
                    ></div>
                </div>
                <div
                    className="mt-1 text-xs text-right"
                    style={{ color: textColor }}
                >
                    {Math.round(percentage)}%
                </div>
            </div>
        </div>
    );
};

export default ProgressBar;
