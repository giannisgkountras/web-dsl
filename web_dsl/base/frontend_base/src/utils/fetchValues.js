import { toast } from "react-toastify";
import convertTypeValue from "./convertTypeValue";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { getValueByPath } from "../utils/getValueByPath";

export const fetchValueFromRest = async (restData, contentPath) => {
    const { name, path, method, params } = restData;

    try {
        const response = await proxyRestCall({ name, path, method, params });
        const value = getValueByPath(response, contentPath);
        return value;
    } catch (error) {
        toast.error(
            "Error fetching or converting REST value: " + error.message
        );
        console.error("REST fetch error:", error);
    }
};

export const fetchValueFromDB = async (dbData, contentPath) => {
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
        return value;
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

export function transformToArrayOfObjects(response, allPaths, keys) {
    const allData = allPaths.map((path) => getValueByPath(response, path));

    if (allData.length === 0 || !allData[0]) {
        throw new Error("No data found at provided paths.");
    }

    if (Array.isArray(allData[0])) {
        // Case: array of values or array of objects
        if (
            typeof allData[0][0] === "object" &&
            !Array.isArray(allData[0][0])
        ) {
            // Already an array of objects
            return allData[0];
        } else {
            // Array of aligned values → zip into array of objects
            return allData[0].map((_, i) => {
                const obj = {};
                keys.forEach((key, j) => {
                    obj[key] = allData[j][i];
                });
                return obj;
            });
        }
    } else if (typeof allData[0] === "object") {
        // Case: object of arrays → convert to array of objects
        const length = Object.values(allData[0])[0]?.length || 0;
        return Array.from({ length }, (_, i) => {
            const obj = {};
            keys.forEach((key, j) => {
                obj[key] = allData[j][key]?.[i];
            });
            return obj;
        });
    } else {
        throw new Error("Unsupported data format.");
    }
}
