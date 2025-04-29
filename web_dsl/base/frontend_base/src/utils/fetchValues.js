import { toast } from "react-toastify";
import convertTypeValue from "./convertTypeValue";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { getValueByPath } from "../utils/getValueByPath";

export const fetchValueFromRest = async (restData, contentPath, setValue) => {
    const { name, path, method, params } = restData;

    try {
        const response = await proxyRestCall({ name, path, method, params });
        const value = getValueByPath(response, contentPath);
        setValue(value);
    } catch (error) {
        toast.error(
            "Error fetching or converting REST value: " + error.message
        );
        console.error("REST fetch error:", error);
    }
};

export const fetchValueFromDB = async (dbData, contentPath, setValue) => {
    const { connection_name, database, query, collection, filter } = dbData;

    try {
        const response = await queryDB({
            connection_name,
            database,
            query,
            collection,
            filter
        });
        const value = getValueByPath(response, contentPath);
        setValue(value);
    } catch (error) {
        toast.error("Error fetching or converting DB value: " + error.message);
        console.error("DB fetch error:", error);
    }
};

export const fetchArrayFromDB = async (dbData, setValue) => {
    const { connection_name, database, query, collection, filter } = dbData;

    try {
        const response = await queryDB({
            connection_name,
            database,
            query,
            collection,
            filter
        });
        setValue(response);
    } catch (error) {
        toast.error("Error fetching or converting DB value: " + error.message);
        console.error("DB fetch error:", error);
    }
};
