import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import { getNameFromPath, getValueByPath } from "../utils/getValueByPath";

const Logs = ({ entityData, attributes = [] }) => {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        if (!entityData) {
            return;
        }
        try {
            if (attributes.length === 0) {
                // If no attributes are provided, set the entire message as JSON data
                setLogs((prev) => [...prev, entityData]);
            } else {
                const newJsonData = {};
                attributes.forEach((attribute) => {
                    const value = getValueByPath(entityData, attribute);
                    const name = getNameFromPath(attribute);
                    newJsonData[name] = value;
                });
                setLogs((prev) => [...prev, newJsonData]);
            }
        } catch (error) {
            toast.error(
                "An error occurred while converting value: " + error.message
            );
        }
    }, [entityData]);

    return (
        <div className="w-full max-h-[500px] overflow-y-auto flex flex-col gap-2 p-4 rounded-2xl shadow-lg">
            <h1 className="text-xl text-white font-semibold mb-2 sticky top-0 z-10">
                Logs
            </h1>

            {[...logs].reverse().map((log, index) => (
                <div
                    key={index}
                    className={`grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-4 p-2 rounded-xl transition 
              ${index % 2 === 0 ? "" : "bg-[#161a23]"}`}
                >
                    {attributes.map((attr) => {
                        const name = getNameFromPath(attr);
                        return (
                            <div
                                key={name}
                                className="flex flex-col items-center text-white text-sm"
                            >
                                <p className="font-semibold">{name}</p>
                                <p className="break-words text-gray-300">
                                    {typeof log[name] === "object"
                                        ? JSON.stringify(log[name])
                                        : log[name] ?? "-"}
                                </p>
                            </div>
                        );
                    })}
                </div>
            ))}
        </div>
    );
};

export default Logs;
