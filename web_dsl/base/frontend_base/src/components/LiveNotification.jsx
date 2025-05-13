import { toast } from "react-toastify";
import { useEffect } from "react";
import { getValueByPath } from "../utils/getValueByPath";

const LiveNotification = ({ entityData, type = "info", contentPath }) => {
    const message = getValueByPath(entityData, contentPath) || "";

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
