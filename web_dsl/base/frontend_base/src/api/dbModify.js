import api from "./index";
import { toast } from "react-toastify";

export const modifyDB = async ({
    connection_name,
    database,
    query,
    collection,
    modification,
    filter,
    new_data,
    dbType
}) => {
    try {
        const payload = {
            connection_name,
            database,
            query: query == {} ? "" : query,
            collection,
            modification,
            filter,
            new_data,
            dbType
        };

        const response = await api.post("modifyDB", payload);

        if (!response) {
            toast.error("No response from proxy.");
            return { status: "error", message: "No response from proxy" };
        }

        toast.success("Database modification successful!");
        return response;
    } catch (error) {
        toast.error("DB modification failed: " + error.message);
        return { status: "error", message: error.message };
    }
};
