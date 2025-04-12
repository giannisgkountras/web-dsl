import api from "./index";
import { toast } from "react-toastify";

export const queryDB = async ({
    connection_name,
    database,
    query,
    collection,
    filter
}) => {
    try {
        const payload = {
            connection_name,
            database,
            query,
            collection,
            filter
        };

        const response = await api.post("queryDB", payload);

        if (!response) {
            toast.error("No response from proxy.");
            return { status: "error", message: "No response from proxy" };
        }
        return response;
    } catch (error) {
        toast.error("Proxy REST call failed: " + error.message);
        return { status: "error", message: error.message };
    }
};
