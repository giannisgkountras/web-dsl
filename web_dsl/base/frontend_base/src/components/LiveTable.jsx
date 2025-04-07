import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useEffect, useRef, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";

const LiveTable = ({ topic, attributes }) => {
    const [logs, setLogs] = useState([]);

    const ws = useContext(WebsocketContext);
    const scrollRef = useRef(null);

    // Handle incoming WebSocket messages using the 'topic' prop
    useWebsocket(ws, topic, (msg) => {
        let newData = {};
        // Dynamically parse the message based on the 'attributes' prop
        attributes.forEach((attr) => {
            newData[attr.name.toLowerCase()] = convertTypeValue(
                msg[attr.name],
                attr.type
            );
        });
        setLogs((prevLogs) => [...prevLogs, newData]);
    });

    // Auto-scroll to the bottom when new logs are added
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    // Utility function to capitalize attribute names for display
    const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

    return (
        <div className="flex text-white justify-center items-center flex-col w-full h-96">
            {/* Titles */}
            <div className="w-full sticky top-0 z-10 border-b">
                <div className="grid grid-cols-[repeat(auto-fit,minmax(100px,1fr))] gap-4 p-2 font-bold">
                    {attributes.map((attr) => (
                        <h1 key={attr.name} className="text-center">
                            {capitalize(attr.name)}
                        </h1>
                    ))}
                </div>
            </div>
            {/* Scrollable Data */}
            <div ref={scrollRef} className="w-full max-h-80 overflow-y-auto">
                {logs.map((log, index) => (
                    <div
                        key={index}
                        className={`grid grid-cols-[repeat(auto-fit,minmax(100px,1fr))] gap-4 p-2 text-center 
                            ${index % 2 === 0 ? "" : "bg-[#161a23]"}`}
                    >
                        {attributes.map((attr) => (
                            <p key={attr.name}>
                                {log[attr.name.toLowerCase()] || "-"}
                            </p>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LiveTable;
