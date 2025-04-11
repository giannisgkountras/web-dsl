import React, { useContext, useEffect, useState } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";

const Alive = ({ topic, timeout }) => {
    const ws = useContext(WebsocketContext);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [status, setStatus] = useState("Offline");

    // When a new message is received, build an object based on the entity's attributes.
    useWebsocket(ws, topic, (msg) => {
        try {
            const now = new Date();
            setStatus("Active");
            setLastUpdated(now);
        } catch (error) {
            toast.error(
                "An error occurred while updating status: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });

    useEffect(() => {
        const interval = setInterval(() => {
            if (lastUpdated && Date.now() - lastUpdated.getTime() < timeout) {
                setStatus("Active");
            } else {
                setStatus("Offline");
            }
        }, 1000);
        return () => clearInterval(interval);
    }, [lastUpdated, timeout]);

    const formattedTimestamp = lastUpdated
        ? lastUpdated.toLocaleString("en-GB", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              hour12: false
          })
        : "N/A";

    return (
        <div className="flex flex-col justify-center items-center">
            <div className="flex justify-evenly items-center">
                <div
                    className={`w-4 h-4 rounded-full ${
                        status === "Active"
                            ? "bg-green-500 animate-pulse"
                            : "bg-red-500"
                    }`}
                ></div>
                <div className="ml-2">{status}</div>
            </div>

            <p>Last Updated: {formattedTimestamp}</p>
        </div>
    );
};

export default Alive;
