import { useState, useContext, useEffect, Fragment } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { getValueByPath } from "../utils/getValueByPath";
import { evaluateConditionWithData } from "../utils/evaluateCondition";

const Condition = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    condition,
    elements
}) => {
    const [showComponent, setShowComponent] = useState(false);
    const contentPath = condition[0];
    const ws = useContext(WebsocketContext);

    const reloadContent = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRest(restData, contentPath);
            setShowComponent(evaluateConditionWithData(condition, data));
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDB(dbData, contentPath);
            setShowComponent(evaluateConditionWithData(condition, data));
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const data = getValueByPath(msg, contentPath);
            setShowComponent(evaluateConditionWithData(condition, data));
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return showComponent
        ? elements.map((el, idx) => <Fragment key={idx}>{el}</Fragment>)
        : null;
};

export default Condition;
