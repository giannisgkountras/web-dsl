import { useContext, useEffect } from "react";
import { useWebsocket } from "../hooks/useWebsocket";
import { WebsocketContext } from "../context/WebsocketContext";
import { toast } from "react-toastify";
import {
    fetchValueFromRestWithoutAccessor,
    fetchValueFromDBWithoutAccessor
} from "../utils/fetchValues";

const Entity = ({
    topic,
    restData,
    dbData,
    sourceOfContent,
    interval,
    setEntityData
}) => {
    const ws = useContext(WebsocketContext);

    const reloadData = async () => {
        if (sourceOfContent === "rest") {
            const data = await fetchValueFromRestWithoutAccessor(restData);
            setEntityData(data);
        }
        if (sourceOfContent === "db") {
            const data = await fetchValueFromDBWithoutAccessor(dbData);
            setEntityData(data);
        }
    };

    useEffect(() => {
        reloadData();

        if (
            interval > 0 &&
            (sourceOfContent === "rest" || sourceOfContent === "db")
        ) {
            const intervalId = setInterval(() => {
                reloadData();
            }, interval);
            return () => clearInterval(intervalId);
        }
    }, []);

    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            setEntityData(msg);
        } catch (error) {
            toast.error(
                "An error occurred while updating value: " + error.message
            );
            console.error("Error updating status:", error);
        }
    });
};

export default Entity;
