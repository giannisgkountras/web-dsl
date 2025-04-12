import React, { useState, useContext } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { GaugeComponent } from "react-gauge-component";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { useEffect } from "react";
import { IoReload } from "react-icons/io5";

const Gauge = ({
    topic,
    attribute,
    sourceOfContent,
    restData,
    staticValue,
    dbData
}) => {
    const ws = useContext(WebsocketContext);
    const [currentValue, setCurrentValue] = useState(0);
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
        if (sourceOfContent === "db") {
            fetchFromDB();
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

    const reloadValue = () => {
        if (sourceOfContent === "rest") {
            fetchValue();
        }
        if (sourceOfContent === "db") {
            fetchFromDB();
        }
    };
    return (
        <div className="flex justify-center items-center relative">
            {(sourceOfContent === "rest" || "db") && (
                <button
                    className="absolute top-0 right-0 p-4 text-gray-100 hover:text-gray-500 hover:cursor-pointer"
                    onClick={reloadValue}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {sourceOfContent === "rest" || sourceOfContent === "broker" ? (
                <GaugeComponent value={currentValue} />
            ) : (
                <GaugeComponent value={staticValue} />
            )}
        </div>
    );
};

export default Gauge;
