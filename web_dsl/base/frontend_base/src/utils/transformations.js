import { getValueByPath } from "./getValueByPath";
import { toast } from "react-toastify";
export const objectOfListsToListOfObjects = (obj) => {
    const keys = Object.keys(obj);
    const length = obj[keys[0]]?.length || 0;
    const result = [];

    for (let i = 0; i < length; i++) {
        const row = {};
        keys.forEach((key) => {
            row[key] = obj[key][i];
        });
        result.push(row);
    }
    return result;
};

export const isObjectOfLists = (obj) => {
    if (typeof obj !== "object" || obj === null || Array.isArray(obj)) {
        return false;
    }

    const values = Object.values(obj);

    // Must contain at least one key with an array value
    if (values.length === 0 || !values.every(Array.isArray)) {
        return false;
    }

    const length = values[0].length;

    // All arrays must be the same length
    return values.every((arr) => arr.length === length);
};

export function transformToArrayOfObjects(response, allPaths, keys) {
    // Check if response is an array of objects
    if (
        Array.isArray(response) &&
        typeof response[0] === "object" &&
        !Array.isArray(response[0])
    ) {
        // Array of objects: e.g., [{x: 1, y1: 10, y2: 0}, {x: 2, y1: 0, y2: 10}]
        const allData = allPaths.map((path) =>
            response.map((obj) => getValueByPath(obj, path))
        );
        return combineData(allData, keys);
    }

    // Check if response is an object of arrays
    if (typeof response === "object" && !Array.isArray(response)) {
        // Object of arrays: e.g., { x: [1, 2], y1: [10, 0], y2: [0, 10] }
        const allData = allPaths.map((path) => getValueByPath(response, path));
        return combineData(allData, keys);
    }

    toast.error("Unsupported data format.");
}

// Helper function to combine data based on paths and keys
function combineData(allData, keys) {
    if (allData.length === 0 || !allData[0]) {
        toast.error("No data found at provided paths.");
    }

    if (Array.isArray(allData[0])) {
        // Case: Array of aligned values → zip into array of objects
        return allData[0].map((_, i) => {
            const obj = {};
            keys.forEach((key, j) => {
                obj[key] = allData[j][i];
            });
            return obj;
        });
    } else if (typeof allData[0] === "object") {
        // Case: Object of arrays → convert to array of objects
        const length = Object.values(allData[0])[0]?.length || 0;
        return Array.from({ length }, (_, i) => {
            const obj = {};
            keys.forEach((key, j) => {
                obj[key] = allData[j][key]?.[i];
            });
            return obj;
        });
    } else {
        toast.error("Unsupported data format.");
    }
}
