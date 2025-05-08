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

export function evaluateComplexCondition(cond, data) {
    if (!Array.isArray(cond) || cond.length === 0) {
        throw new Error("Invalid condition format: must be a non-empty array");
    }

    const head = cond[0];

    // Logical AND
    if (head === "and") {
        const [, leftCond, rightCond] = cond;
        // short-circuit: if left is false, no need to eval right
        if (!evaluateComplexCondition(leftCond, data)) {
            return false;
        }
        return evaluateComplexCondition(rightCond, data);
    }

    // Logical OR
    if (head === "or") {
        const [, leftCond, rightCond] = cond;
        // short-circuit: if left is true, no need to eval right
        if (evaluateComplexCondition(leftCond, data)) {
            return true;
        }
        return evaluateComplexCondition(rightCond, data);
    }

    // Comparison node: [rawLeft, op, rawRight]
    if (cond.length === 3) {
        let [rawLeft, op, rawRight] = cond;

        // resolve left side (path → value, or literal)
        let leftVal = Array.isArray(rawLeft)
            ? getValueByPath(data, rawLeft)
            : rawLeft;
        if (leftVal === undefined) {
            leftVal = false;
        }
        if (leftVal === "true") {
            leftVal = true;
        }
        if (leftVal === "false") {
            leftVal = false;
        }

        // resolve right side  (path → value, or literal)
        let rightVal = Array.isArray(rawRight)
            ? getValueByPath(data, rawRight)
            : rawRight;
        if (rightVal === undefined) {
            rightVal = false;
        }
        if (rightVal === "true") {
            rightVal = true;
        }
        if (rightVal === "false") {
            rightVal = false;
        }

        return comparePrimitives(leftVal, op, rightVal);
    }

    throw new Error(`Unexpected condition node: ${JSON.stringify(cond)}`);
}

function comparePrimitives(left, op, right) {
    switch (op) {
        case "==":
            return left === right;
        case "!=":
            return left !== right;
        case ">":
            return left > right;
        case "<":
            return left < right;
        case ">=":
            return left >= right;
        case "<=":
            return left <= right;
        default:
            throw new Error(`Unsupported comparison operator "${op}"`);
    }
}
