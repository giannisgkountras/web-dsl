import { toast } from "react-toastify";

const convertTypeValue = (value, type) => {
    try {
        if (value === undefined || value === null) {
            throw new Error("Cannot convert undefined or null to object");
        }

        switch (type) {
            case "IntAttribute":
                return isNaN(parseInt(value, 10)) ? 0 : parseInt(value, 10);
            case "FloatAttribute":
                return isNaN(parseFloat(value)) ? 0.0 : parseFloat(value);
            case "BoolAttribute":
                return value === "true" || value === true;
            default:
                return value ?? ""; // Fallback to an empty string for unknown types
        }
    } catch (error) {
        toast.error(error.message);
        console.error("Conversion Error:", error);

        // Return a safe default value to avoid breaking further operations
        switch (type) {
            case "IntAttribute":
                return 0;
            case "FloatAttribute":
                return 0.0;
            case "BoolAttribute":
                return false;
            default:
                return "";
        }
    }
};

export default convertTypeValue;
