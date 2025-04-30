import { toast } from "react-toastify";

export const getValueByPath = (obj, path) => {
    try {
        const result = path.reduce((acc, key) => {
            if (acc && key in acc) {
                return acc[key];
            } else {
                throw new Error(`Invalid path at key: ${key}`);
            }
        }, obj);
        return result;
    } catch (error) {
        toast.error(error.message);
        return undefined;
    }
};

export const getNameFromPath = (path) => {
    if (!Array.isArray(path) || path.length === 0) return "unknown";

    // Find the last string in the path (the last key, not an index)
    for (let i = path.length - 1; i >= 0; i--) {
        if (typeof path[i] === "string") {
            return path[i];
        }
    }

    // If no string key is found (only indices), fallback
    return `value_${path.join("_")}`;
};
