import { getValueByPath } from "./getValueByPath";
import { toast } from "react-toastify";

export function evaluateComplexCondition(cond, data) {
    if (typeof cond === "boolean") {
        return cond;
    }

    if (cond === "true") {
        return true;
    }
    if (cond === "false") {
        return false;
    }

    if (!Array.isArray(cond) || cond.length === 0) {
        toast.error("Invalid condition format: must be a non-empty array");
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

    toast.error(`Unexpected condition node: ${JSON.stringify(cond)}`);
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
            toast.error(`Unsupported comparison operator "${op}"`);
    }
}
