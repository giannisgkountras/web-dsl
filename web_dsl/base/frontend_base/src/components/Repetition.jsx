import { useState, useEffect, cloneElement } from "react";
import { getValueByPath } from "../utils/getValueByPath";
import { evaluateComplexCondition } from "../utils/evaluateCondition";

const Repetition = ({
    allDataNeededFromEntities,
    item,
    element,
    conditionDataPath = "",
    dataPath = null,
    condition = true,
    elementElse = <></>,
    dataElsePath = null,
    orientation
}) => {
    const contentPath = item;
    const [allData, setAllData] = useState();

    useEffect(() => {
        const values = Object.values(allDataNeededFromEntities);
        const allUndefined = values.every((value) => value === undefined);
        if (allUndefined) {
            return;
        }
        const data = getValueByPath(allDataNeededFromEntities, contentPath);
        setAllData(data);
    }, [allDataNeededFromEntities]);

    return (
        <div
            className="flex justify-evenly items-center w-full relative"
            style={{ flexDirection: orientation }}
        >
            {Array.isArray(allData) ? (
                allData.map((item, idx) => (
                    <div
                        key={idx}
                        className="flex w-full justify-center items-center"
                    >
                        {evaluateComplexCondition(condition, item)
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
