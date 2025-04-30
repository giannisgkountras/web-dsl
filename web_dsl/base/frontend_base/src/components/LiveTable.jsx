import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useEffect, useRef, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";

const LiveTable = ({ topic, columns }) => {
    const [logs, setLogs] = useState([]);
    const [names, setNames] = useState([]);
    const ws = useContext(WebsocketContext);

    // Handle incoming WebSocket messages using the 'topic' prop
    useWebsocket(ws, topic, (msg) => {
        let newData = {};
        let newNames = [];
        // Dynamically parse the message based on the 'attributes' prop
        columns.forEach((column) => {
            const value = getValueByPath(msg, column);
            const name = getNameFromPath(column); // <- name from path
            newData[name] = value;
            newNames.push(name);
        });
        setLogs((prevLogs) => [...prevLogs, newData]);
        setNames(newNames);
    });

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
