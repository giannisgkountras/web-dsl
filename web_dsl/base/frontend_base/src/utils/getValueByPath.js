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
