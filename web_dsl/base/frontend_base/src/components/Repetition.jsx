import { useState, useContext, useEffect, Fragment, cloneElement } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import { fetchValueFromRest, fetchValueFromDB } from "../utils/fetchValues";
import { getValueByPath } from "../utils/getValueByPath";
import { evaluateConditionWithData } from "../utils/evaluateCondition";
import { IoReload } from "react-icons/io5";

const Repetition = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    item,
    element,
    conditionDataPath = "",
    dataPath = null,
    condition = true,
    elementElse = <></>,
    dataElsePath = null,
    orientation,
    interval
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
        if (
            interval > 0 &&
            (sourceOfContent === "rest" || sourceOfContent === "db")
        ) {
            const intervalId = setInterval(() => {
                reloadContent();
            }, interval);
            return () => clearInterval(intervalId);
        }
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
    return (
        <div
            className="flex justify-evenly items-center w-full relative"
            style={{ flexDirection: orientation }}
        >
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    className="absolute top-0 right-0 text-gray-100 hover:text-gray-500 hover:cursor-pointer box-content"
                    onClick={reloadContent}
                    title="Refresh Value"
                >
                    <IoReload size={24} />
                </button>
            )}
            {Array.isArray(allData) ? (
                allData.map((item, idx) => (
                    <div
                        key={idx}
                        className="flex w-full justify-center items-center"
                    >
                        {evaluateConditionWithData(
                            condition,
                            getValueByPath(item, conditionDataPath)
                        )
                            ? cloneElement(
                                  element,
                                  dataPath !== null
                                      ? {
                                            repetitionItem: getValueByPath(
                                                item,
                                                dataPath
                                            )
                                        }
                                      : {}
                              )
                            : cloneElement(
                                  elementElse,
                                  dataElsePath !== null
                                      ? {
                                            repetitionItem: getValueByPath(
                                                item,
                                                dataElsePath
                                            )
                                        }
                                      : {}
                              )}
                    </div>
                ))
            ) : (
                <p className="text-red-500">No data found</p>
            )}
        </div>
    );
};
export default Repetition;
