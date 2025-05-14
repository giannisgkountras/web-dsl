import { toast } from "react-toastify";
import { useState, useEffect } from "react";
import { getValueByPath } from "../utils/getValueByPath";

const LiveNotification = ({ entityData, type = "info", contentPath }) => {
    const [message, setMessage] = useState("");
    useEffect(() => {
        if (!entityData) {
            return;
        }
        setMessage(getValueByPath(entityData, contentPath));
    }, [entityData]);

    const notify = {
        success: () => toast.success(message),
        error: () => toast.error(message),
        info: () => toast.info(message),
        warning: () => toast.warning(message)
    };

    useEffect(() => {
        if (message !== "") {
            notify[type]();
        }
    }, [message]);
};

export default LiveNotification;
