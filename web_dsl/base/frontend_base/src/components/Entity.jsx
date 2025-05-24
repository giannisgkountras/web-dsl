import { useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import {
    fetchValueFromRestWithoutAccessor,
    fetchValueFromDBWithoutAccessor
} from "../utils/fetchValues";
import { evaluateExpression } from "../utils/evaluateComputations";

const Entity = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    interval,
    setEntityData,
    computedAttributes
}) => {
    const ws = useContext(WebsocketContext);

    const reloadData = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRestWithoutAccessor(restData);
            setEntityData(data);
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDBWithoutAccessor(dbData);
            setEntityData(data);
        }
    };

    useEffect(() => {
        reloadData();

        if (
            interval > 0 &&
            (sourceOfContent === "rest" || sourceOfContent === "db")
        ) {
            const intervalId = setInterval(() => {
                reloadData();
            }, interval);
            return () => clearInterval(intervalId);
        }
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            let currentData = msg; // Data from WebSocket

            // Calcualte all results of computed attributes
            const computedResults = computedAttributes.map((attribute) => {
                const { name, expression } = attribute;
                const evaluatedValue = evaluateExpression(
                    expression,
                    currentData
                );
                return { name, value: evaluatedValue };
            });
            // Append computed results to currentData
            computedResults.forEach((result) => {
                currentData[result.name] = result.value;
            });
            console.log("Final data after evaluation:", computedResults);

            setEntityData(currentData);
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
};

export default Entity;
