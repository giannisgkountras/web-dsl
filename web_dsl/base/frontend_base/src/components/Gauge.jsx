import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { GaugeComponent } from "react-gauge-component";
import { toast } from "react-toastify";
import { useEffect } from "react";
import { IoReload } from "react-icons/io5";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { getValueByPath } from "../utils/getValueByPath";

const Gauge = ({
    topic,
    attribute,
    sourceOfContent,
    restData,
    staticValue,
    dbData,
    contentPath
}) => {
    const ws = useContext(WebsocketContext);
    const [currentValue, setCurrentValue] = useState(0);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setCurrentValue(getValueByPath(msg, contentPath));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    const reloadValue = () => {
        if (sourceOfContent === "rest") {
            fetchValueFromRest(restData, contentPath, setCurrentValue);
        }
        if (sourceOfContent === "db") {
            fetchValueFromDB(dbData, contentPath, setCurrentValue);
        }
    };

    useEffect(() => {
        reloadValue();
    }, []);

    return (
        <div className="flex justify-center items-center relative">
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={reloadValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {sourceOfContent === "static" ? (
                <GaugeComponent value={staticValue} />
            ) : (
                <GaugeComponent value={currentValue} />
            )}
        </div>
    );
};

export default Gauge;
