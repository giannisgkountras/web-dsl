import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { GaugeComponent } from "react-gauge-component";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { useEffect } from "react";
import { IoReload } from "react-icons/io5";

const Gauge = ({ topic, attribute, sourceOfContent, restData }) => {
    const ws = useContext(WebsocketContext);
    const [currentValue, setCurrentValue] = useState(0);
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
                    const value = convertTypeValue(
                        response[attribute.name],
                        attribute.type
                    );
                    setCurrentValue(value);
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
            setCurrentValue(
                convertTypeValue(msg[attribute.name], attribute.type)
            );
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return (
        <div className="flex justify-center items-center relative">
            {"rest" === sourceOfContent && (
                <button
                    className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={fetchValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            <GaugeComponent value={currentValue} />
        </div>
    );
};

export default Gauge;
