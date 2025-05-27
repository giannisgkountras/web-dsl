import { getValueByPath } from "./getValueByPath";
import { toast } from "react-toastify";

const ARITHMETIC_OPERATORS_AND_FUNCTIONS = [
    "+",
    "-",
    "*",
    "/",
    "sum",
    "mean",
    "max",
    "min",
    "round",
    "sortasc",
    "sortdesc",
    "reverse",
    "length",
    "slice"
];

const customMathForEval = {
    sum: (...args) =>
        args
            .filter((arg) => typeof arg === "number" && !isNaN(arg))
            .reduce((a, b) => a + b, 0),
    mean: (...args) => {
        const numericArgs = args.filter(
            (arg) => typeof arg === "number" && !isNaN(arg)
        );
        if (numericArgs.length === 0) return NaN;
        return numericArgs.reduce((a, b) => a + b, 0) / numericArgs.length;
    }
};

function resolveOperandInternal(operand, data, evaluateFunc) {
    if (typeof operand === "number" || typeof operand === "string") {
        return operand;
    }

    if (Array.isArray(operand)) {
        if (operand.length === 0) {
            toast.error("Empty array encountered as operand.");
            return [];
        }
        const head = operand[0];
        // Check if it's a nested expression (e.g., ['*', ['x'], 2])
        if (
            typeof head === "string" &&
            ARITHMETIC_OPERATORS_AND_FUNCTIONS.includes(head.toLowerCase())
        ) {
            return evaluateFunc(operand, data); // Recursively evaluate the nested expression
        } else {
            // Assume it's a path array (e.g., ['x', 'test'] or ['temperatures'])
            const value = getValueByPath(data, operand);

            if (value === undefined) {
                toast.error(
                    `Path ${JSON.stringify(operand)} resolved to undefined.`
                );
                return NaN;
            }

            return value;
        }
    }

    // Unsupported operand types (e.g., direct strings not from paths, booleans, plain objects)
    toast.error(
        `Unsupported operand type: ${typeof operand} (${JSON.stringify(
            operand
        )})`
    );
    return NaN;
}

export function evaluateExpression(expression, data) {
    // Case 1: Expression is a literal number or string
    if (typeof expression === "number" || typeof expression === "string") {
        return expression;
    }

    // Case 2: Expression is an Array (operation or path)
    if (Array.isArray(expression)) {
        if (expression.length === 0) {
            toast.error("Cannot evaluate empty array expression.");
            return NaN;
        }

        const operatorCandidate = expression[0];

        // Subcase 2a: Array is an operation array
        if (
            typeof operatorCandidate === "string" &&
            ARITHMETIC_OPERATORS_AND_FUNCTIONS.includes(
                operatorCandidate.toLowerCase()
            )
        ) {
            const operator = operatorCandidate.toLowerCase();
            const rawOperands = expression.slice(1);

            const resolvedOperands = rawOperands.map((rawOp) =>
                resolveOperandInternal(rawOp, data, evaluateExpression)
            );

            // --- Handle operation categories ---

            // A. Aggregate (sum, mean, max, min)
            if (["sum", "mean", "max", "min"].includes(operator)) {
                const numbersToProcess = [];
                resolvedOperands.forEach((op) => {
                    if (typeof op === "number" && !isNaN(op)) {
                        numbersToProcess.push(op);
                    } else if (Array.isArray(op)) {
                        op.forEach((item) => {
                            if (typeof item === "number" && !isNaN(item)) {
                                numbersToProcess.push(item);
                            }
                        });
                    }
                });

                switch (operator) {
                    case "sum":
                        return customMathForEval.sum(...numbersToProcess);
                    case "mean":
                        return customMathForEval.mean(...numbersToProcess);
                    case "max":
                        return numbersToProcess.length > 0
                            ? Math.max(...numbersToProcess)
                            : NaN;
                    case "min":
                        return numbersToProcess.length > 0
                            ? Math.min(...numbersToProcess)
                            : NaN;
                }
            }

            // B. Basic Arithmetic (+, -, *, /)
            else if (["+", "-", "*", "/"].includes(operator)) {
                const numericOperands = resolvedOperands.map((op) => {
                    if (typeof op !== "number" || isNaN(op)) return NaN;
                    return op;
                });
                if (numericOperands.some(isNaN)) return NaN;

                switch (operator) {
                    case "+":
                        return numericOperands.reduce((s, v) => s + v, 0);
                    case "-":
                        if (numericOperands.length === 1)
                            return -numericOperands[0];
                        if (numericOperands.length === 2)
                            return numericOperands[0] - numericOperands[1];
                        return NaN;
                    case "*":
                        return numericOperands.reduce((p, v) => p * v, 1);
                    case "/":
                        if (
                            numericOperands.length !== 2 ||
                            numericOperands[1] === 0
                        )
                            return NaN;
                        return numericOperands[0] / numericOperands[1];
                }
            }

            // C. New Array/Util Operations (sortasc, sortdesc, reverse, length, round)
            else if (
                ["sortasc", "sortdesc", "reverse", "length", "round"].includes(
                    operator
                )
            ) {
                switch (operator) {
                    case "sortasc":
                    case "sortdesc": // Expects: sortasc(array) or sortdesc(array)
                        const arrayToSort = resolvedOperands[0];
                        if (!Array.isArray(arrayToSort)) {
                            console.error(
                                `'${operator}' expects an array as its argument.`
                            );
                            return NaN;
                        }
                        const copyToSort = [...arrayToSort]; // Make a copy

                        // Determine sort order based on operator
                        const sortOrder =
                            operator === "sortasc" ? "asc" : "desc";

                        if (copyToSort.every((el) => typeof el === "number")) {
                            return copyToSort.sort((a, b) =>
                                sortOrder === "asc" ? a - b : b - a
                            );
                        } else if (
                            copyToSort.every((el) => typeof el === "string")
                        ) {
                            return copyToSort.sort((a, b) =>
                                sortOrder === "asc"
                                    ? a.localeCompare(b)
                                    : b.localeCompare(a)
                            );
                        } else {
                            console.error(
                                `'${operator}' currently supports arrays of all numbers or all strings.`
                            );
                            return NaN;
                        }

                    case "reverse": // Expects: reverse(array)
                        const arrayToReverse = resolvedOperands[0];
                        if (!Array.isArray(arrayToReverse)) return NaN;
                        return [...arrayToReverse].reverse();

                    case "length": // Expects: length(arrayOrString) or length(item1, item2, ...)
                        const firstOpForLength = resolvedOperands[0];
                        if (
                            resolvedOperands.length === 1 &&
                            (Array.isArray(firstOpForLength) ||
                                typeof firstOpForLength === "string")
                        ) {
                            return firstOpForLength.length;
                        } else {
                            return resolvedOperands.filter(
                                (op) => op !== undefined && !Number.isNaN(op)
                            ).length;
                        }

                    case "round": // Expects: round(number, decimals?)
                        // ... (logic for round as before) ...
                        const numberToRound = resolvedOperands[0];
                        const decimals = resolvedOperands[1];
                        if (
                            typeof numberToRound !== "number" ||
                            isNaN(numberToRound)
                        )
                            return NaN;
                        const numDecimals =
                            typeof decimals === "number" &&
                            !isNaN(decimals) &&
                            Number.isInteger(decimals) &&
                            decimals >= 0
                                ? decimals
                                : 0;
                        const factor = Math.pow(10, numDecimals);
                        return Math.round(numberToRound * factor) / factor;
                }
            } else if (["slice"].includes(operator)) {
                const targetString = resolvedOperands[0];
                if (typeof targetString !== "string") {
                    toast.error(
                        `Operator '${operator}' expects a string as its first argument.`
                    );
                    return NaN; // Or an empty string, or the original non-string value
                }

                switch (operator) {
                    case "slice": // slice(string, startIndex, endIndex?)
                        const startIndex = resolvedOperands[1];
                        const endIndex = resolvedOperands[2]; // endIndex is optional for String.prototype.slice

                        if (
                            typeof startIndex !== "number" ||
                            isNaN(startIndex)
                        ) {
                            // toast.error("Slice 'startIndex' must be a number.");
                            // console.warn("Slice 'startIndex' must be a number.");
                            return targetString; // Or NaN, or empty string
                        }

                        if (
                            endIndex !== undefined &&
                            (typeof endIndex !== "number" || isNaN(endIndex))
                        ) {
                            // toast.error("Slice 'endIndex', if provided, must be a number.");
                            // console.warn("Slice 'endIndex', if provided, must be a number.");
                            return targetString.slice(startIndex); // Or NaN, or empty string
                        }
                        // String.prototype.slice handles undefined endIndex correctly
                        return targetString.slice(startIndex, endIndex);
                }
            }
            // Fallback for unhandled
            // console.warn(`Operator '${operatorCandidate}' is listed but not explicitly handled in a category.`);
            return NaN;
        } else {
            // Subcase 2b: Array is not an operation array, so treat it as a path.
            const value = getValueByPath(data, expression);
            if (value === undefined) return NaN;
            return value;
        }
    }
    // Case 3: Expression is of an unsupported type - REMAINS THE SAME
    toast.error(
        `Unsupported expression type: ${typeof expression} (${JSON.stringify(
            expression
        )})`
    );
    return NaN;
}
