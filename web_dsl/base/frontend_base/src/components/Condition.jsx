import { useState, useContext, useEffect, Fragment } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import {
    fetchValueFromRestWithoutAccessor,
    fetchValueFromDBWithoutAccessor
} from "../utils/fetchValues";
import { evaluateComplexCondition } from "../utils/evaluateCondition";

const Condition = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    condition,
    elements,
    elementsElse = <></>,
    interval
}) => {
    const [showComponent, setShowComponent] = useState(false);
    const ws = useContext(WebsocketContext);

    const reloadContent = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRestWithoutAccessor(restData);
            setShowComponent(evaluateComplexCondition(condition, data));
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDBWithoutAccessor(dbData);
            setShowComponent(evaluateComplexCondition(condition, data));
        }
    };

    useEffect(() => {
        reloadContent();
        if (interval !== null && interval > 0) {
            // Set up an interval to reload content
            const intervalId = setInterval(() => {
                reloadContent();
            }, interval);
            return () => clearInterval(intervalId);
        }
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setShowComponent(evaluateComplexCondition(condition, msg));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return showComponent
        ? elements.map((el, idx) => <Fragment key={idx}>{el}</Fragment>)
        : elementsElse.map((el, idx) => <Fragment key={idx}>{el}</Fragment>);
};

export default Condition;
