import { toast } from "react-toastify";

const convertTypeValue = (value, type) => {
    try {
        if (value === undefined || value === null) {
            throw new Error("Cannot convert undefined or null to object");
        }

        switch (type) {
            case "IntAttribute":
                return parseInt(value, 10);
            case "FloatAttribute":
                return parseFloat(value);
            case "BoolAttribute":
                return value === "true" || value === true;
            default:
                return value;
        }
    } catch (error) {
        toast.error(error.message);
        console.error("Conversion Error:", error);
        return null; // Return a fallback value if conversion fails
    }
};

export default convertTypeValue;
