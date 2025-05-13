import { useEffect, useState } from "react";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";

const LiveTable = ({ entityData, columns }) => {
    const [logs, setLogs] = useState([]);
    const [names, setNames] = useState([]);

    useEffect(() => {
        const newData = {};
        const newNames = [];
        columns.forEach((column) => {
            const value = getValueByPath(entityData, column);
            const name = getNameFromPath(column); // <- name from path
            newData[name] = value;
            newNames.push(name);
        });
        setLogs((prevLogs) => [...prevLogs, newData]);
        setNames(newNames);
    }, [entityData]);

    // Utility function to capitalize attribute names for display
    const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

    return (
        <div className="flex text-white justify-center items-center flex-col w-full h-96">
            {/* Titles */}
            <div className="w-full sticky top-0 z-10 border-b">
                <div className="grid grid-cols-[repeat(auto-fit,minmax(100px,1fr))] gap-4 p-2 font-bold">
                    {names.map((name, idx) => (
                        <h1 key={idx} className="text-center">
                            {capitalize(name)}
                        </h1>
                    ))}
                </div>
            </div>
            {/* Scrollable Data */}
            <div className="w-full max-h-80 overflow-y-auto">
                {[...logs].reverse().map((log, index) => (
                    <div
                        key={index}
                        className={`grid grid-cols-[repeat(auto-fit,minmax(100px,1fr))] gap-4 p-2 text-center 
                ${index % 2 === 0 ? "" : "bg-[#161a23]"}`}
                    >
                        {names.map((name) => (
                            <p key={name}>
                                {log[name] !== undefined && log[name] !== null
                                    ? typeof log[name] === "object"
                                        ? JSON.stringify(log[name])
                                        : log[name]
                                    : "-"}
                            </p>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LiveTable;
