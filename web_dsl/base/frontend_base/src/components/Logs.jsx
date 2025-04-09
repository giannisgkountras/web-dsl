import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";
import { toast } from "react-toastify";

const Logs = ({ topic, attributes = [] }) => {
    const [logs, setLogs] = useState([]);
    const ws = useContext(WebsocketContext);

    // Handle incoming WebSocket messages using the 'topic' prop
    useWebsocket(ws, topic, (msg) => {
        if (attributes.length === 0) {
            // If no attributes are provided, set the entire message as JSON data
            try {
                setLogs((prev) => [...prev, msg]);
            } catch (error) {
                toast.error(
                    "An error occurred while updating value: " + error.message
                );
                console.error("Error updating logs:", error);
            }
        } else {
            const newJsonData = {};
            attributes.forEach((attribute) => {
                try {
                    newJsonData[attribute.name] = convertTypeValue(
                        msg[attribute.name],
                        attribute.type
                    );
                } catch (error) {
                    toast.error(
                        "An error occurred while updating value: " +
                            error.message
                    );
                    console.error("Error updating logs:", error);
                }
            });
            setLogs((prev) => [...prev, newJsonData]);
        }
    });

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
                    {attributes.map((attr) => (
                        <div
                            key={attr.name}
                            className="flex flex-col items-center text-white text-sm"
                        >
                            <p className="font-semibold">{attr.name}</p>
                            <p className="break-words text-gray-300">
                                {log[attr.name.toLowerCase()] || "-"}
                            </p>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

export default Logs;
