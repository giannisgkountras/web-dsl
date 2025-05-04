import { getValueByPath } from "./getValueByPath";
import { toast } from "react-toastify";

const operatorMaps = {
    "==": (a, b) => a == b,
    "===": (a, b) => a === b,
    "!=": (a, b) => a != b,
    "!==": (a, b) => a !== b,
    "<": (a, b) => a < b,
    "<=": (a, b) => a <= b,
    ">": (a, b) => a > b,
    ">=": (a, b) => a >= b
};

export const evaluateCondition = (condition, data) => {
    if (condition === undefined || condition === null) {
        return true;
    }

    if (typeof condition === "boolean") {
        return condition;
    }

    if (Array.isArray(condition)) {
        const [conditionPath, conditionOperator, conditionValue] = condition;
        const value = getValueByPath(data, conditionPath);

        if (value === undefined) {
            return false;
        }

        const comparator = operatorMaps[conditionOperator];
        if (!comparator) {
            toast.warn(`Unknown operator: ${conditionOperator}`);
            return false;
        }

        return comparator(value, conditionValue);
    }

    toast.warn("Invalid condition format:", condition);
    return false;
};

export const evaluateConditionWithData = (condition, data) => {
    if (condition === undefined || condition === null) {
        return true;
    }

    if (typeof condition === "boolean") {
        return condition;
    }

    if (condition === "true") {
        return true;
    }
    if (condition === "false") {
        return false;
    }

    if (Array.isArray(condition)) {
        const [conditionPath, conditionOperator, conditionValue] = condition;

        let finalConditionValue = conditionValue;
        if (conditionValue === "true") {
            finalConditionValue = true;
        } else if (conditionValue === "false") {
            finalConditionValue = false;
        }

        const comparator = operatorMaps[conditionOperator];
        if (!comparator) {
            toast.warn(`Unknown operator: ${conditionOperator}`);
            return false;
        }

        return comparator(data, finalConditionValue);
    }

    toast.warn("Invalid condition format:", condition);
    return false;
};
