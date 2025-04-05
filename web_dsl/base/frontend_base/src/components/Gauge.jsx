import React, { useState } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import convertTypeValue from "../utils/convertTypeValue";
import { GaugeComponent } from "react-gauge-component";

const Gauge = ({ topic, attribute }) => {
    const ws = useContext(WebsocketContext);
    const [currentValue, setCurrentValue] = useState();

    useWebsocket(ws, topic, (msg) => {
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
    return <GaugeComponent value={currentValue} />;
};

export default Gauge;
