import { useState, useContext, useEffect, Fragment, cloneElement } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { getValueByPath } from "../utils/getValueByPath";
import { evaluateConditionWithData } from "../utils/evaluateCondition";
const Repetition = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    item,
    element,
    dataPath = [],
    condition = true
}) => {
    const contentPath = item;
    const ws = useContext(WebsocketContext);
    const [allData, setAllData] = useState();
    const reloadContent = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRest(restData, contentPath);
            setAllData(data);
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDB(dbData, contentPath);
            setAllData(data);
        }
    };

    useEffect(() => {
        reloadContent();
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const data = getValueByPath(msg, contentPath);
            setAllData(data);
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
    return Array.isArray(allData) ? (
        allData.map((item, idx) =>
            evaluateConditionWithData(
                condition,
                getValueByPath(item, dataPath)
            ) === false ? null : (
                <Fragment key={idx}>
                    {cloneElement(element, {
                        repetitionItem: getValueByPath(item, dataPath)
                    })}
                </Fragment>
            )
        )
    ) : (
        <p className="text-red-500">No data found</p>
    );
};

export default Repetition;
