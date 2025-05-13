import { useEffect, useState } from "react";

const Alive = ({ entityData, timeout, description }) => {
    const [lastUpdated, setLastUpdated] = useState(null);
    const [status, setStatus] = useState("Offline");

    useEffect(() => {
        const now = new Date();
        setStatus("Active");
        setLastUpdated(now);
    }, [entityData]);

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
            {description && (
                <h1 className="text-lg font-semibold mb-2">{description}</h1>
            )}
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
