import { getValueByPath } from "./getValueByPath"; // Assuming this is your actual import

const ARITHMETIC_OPERATORS_AND_FUNCTIONS = [
    "+",
    "-",
    "*",
    "/",
    "sum",
    "mean",
    "max",
    "min"
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

function resolveArithmeticOperandInternal(operand, data, evaluateFunc) {
    if (typeof operand === "number") {
        return operand; // Literal number
    }

    if (Array.isArray(operand)) {
        if (operand.length === 0) {
            // console.error("Empty array encountered as operand.");
            return NaN;
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
                // console.error(`Path ${JSON.stringify(operand)} resolved to undefined.`);
                return NaN;
            }

            // If the path resolves to a single number, return it.
            if (typeof value === "number" && !isNaN(value)) {
                return value;
            }

            // If the path resolves to an array, check if it's an array of numbers.
            if (Array.isArray(value)) {
                if (
                    value.every(
                        (item) => typeof item === "number" && !isNaN(item)
                    )
                ) {
                    return value; // Return the array of numbers itself
                } else {
                    // Path resolved to an array of non-numbers or mixed types
                    // console.error(`Path ${JSON.stringify(operand)} resolved to an array not purely of numbers: ${JSON.stringify(value)}.`);
                    return NaN;
                }
            }

            // Path resolved to something not usable in arithmetic (string, object, etc.)
            // console.error(`Path ${JSON.stringify(operand)} resolved to non-numeric/non-array value: ${JSON.stringify(value)}.`);
            return NaN;
        }
    }

    // Unsupported operand types
    // console.error(`Unsupported operand type: ${typeof operand} (${JSON.stringify(operand)})`);
    return NaN;
}

export function evaluateArithmeticArray(expression, data) {
    // Case 1: Expression is a literal number
    if (typeof expression === "number") {
        return expression;
    }

    // Case 2: Expression is an Array
    if (Array.isArray(expression)) {
        if (expression.length === 0) {
            // console.error("Cannot evaluate empty array expression.");
            return NaN;
        }

        const operatorCandidate = expression[0];

        // Subcase 2a: Array is an operation array (e.g., ['+', 1, 2] or ['sum', ['temperatures']])
        if (
            typeof operatorCandidate === "string" &&
            ARITHMETIC_OPERATORS_AND_FUNCTIONS.includes(
                operatorCandidate.toLowerCase()
            )
        ) {
            const operator = operatorCandidate.toLowerCase();
            const rawOperands = expression.slice(1);

            const resolvedOperands = rawOperands.map((rawOp) =>
                resolveArithmeticOperandInternal(
                    rawOp,
                    data,
                    evaluateArithmeticArray
                )
            );

            // Handle functions that operate on collections (sum, mean, max, min)
            if (["sum", "mean", "max", "min"].includes(operator)) {
                const numbersToProcess = [];
                for (const op of resolvedOperands) {
                    if (typeof op === "number" && !isNaN(op)) {
                        numbersToProcess.push(op);
                    } else if (Array.isArray(op)) {
                        // op is an array of numbers
                        numbersToProcess.push(...op); // Spread its elements
                    } else if (isNaN(op)) {
                        // An operand resolved to NaN
                        numbersToProcess.push(NaN); // Propagate NaN to be filtered by robust math functions
                    }
                    // Other types (e.g. string from a bad path) would have become NaN in resolveArithmeticOperandInternal
                }

                // Filter out NaNs for Math.max/min, sum/mean are already robust
                const finalNumericArgs = numbersToProcess.filter(
                    (n) => typeof n === "number" && !isNaN(n)
                );

                switch (operator) {
                    case "sum":
                        return customMathForEval.sum(...finalNumericArgs);
                    case "mean":
                        return customMathForEval.mean(...finalNumericArgs);
                    case "max":
                        return finalNumericArgs.length > 0
                            ? Math.max(...finalNumericArgs)
                            : NaN;
                    case "min":
                        return finalNumericArgs.length > 0
                            ? Math.min(...finalNumericArgs)
                            : NaN;
                }
            }
            // Handle standard arithmetic operators (+, -, *, /)
            else if (["+", "-", "*", "/"].includes(operator)) {
                // These operators expect single numeric operands.
                // Check if any resolvedOperand is an array (which is not allowed here).
                const numericOperands = resolvedOperands.map((op) => {
                    if (typeof op !== "number" || isNaN(op)) {
                        // If op is an array or NaN (e.g. ['+', ['list'], 5] -> op for ['list'] is [1,2,3])
                        // console.error(`Operator '${operator}' expects numeric operands. Found: ${JSON.stringify(op)}`);
                        return NaN;
                    }
                    return op;
                });

                if (numericOperands.some(isNaN)) {
                    // If any operand was not a valid number for these ops
                    return NaN;
                }

                switch (operator) {
                    case "+":
                        return numericOperands.reduce(
                            (sum, val) => sum + val,
                            0
                        );
                    case "-":
                        if (numericOperands.length === 1)
                            return -numericOperands[0];
                        if (numericOperands.length === 2)
                            return numericOperands[0] - numericOperands[1];
                        // console.error(`'-' operator requires 1 or 2 numeric operands, found ${numericOperands.length}.`);
                        return NaN;
                    case "*":
                        return numericOperands.reduce(
                            (product, val) => product * val,
                            1
                        );
                    case "/":
                        if (numericOperands.length !== 2) {
                            // console.error(`'/' operator requires exactly 2 numeric operands, found ${numericOperands.length}.`);
                            return NaN;
                        }
                        const [dividend, divisor] = numericOperands;
                        if (divisor === 0) {
                            // console.error("Division by zero.");
                            return NaN;
                        }
                        return dividend / divisor;
                }
            } else {
                // Should not be reached if ARITHMETIC_OPERATORS_AND_FUNCTIONS is correct
                // console.error(`Unsupported operator in expression processing: ${operatorCandidate}`);
                return NaN;
            }
        } else {
            // Subcase 2b: Array is not an operation array, treat it as a path.
            // This function (evaluateArithmeticArray) is expected to return a single number or NaN.
            // If a path resolves to an array (e.g. evaluateArithmeticArray(['temperatures'], data)),
            // it's not a single number, so it should result in NaN in this direct context.
            // An array value from a path is only useful when it's an *operand* to sum/mean/max/min.
            const value = getValueByPath(data, expression);
            if (value === undefined) {
                // console.error(`Path ${JSON.stringify(expression)} resolved to undefined.`);
                return NaN;
            }
            // Expect single number when evaluateArithmeticArray is called directly on a path
            if (typeof value !== "number" || isNaN(value)) {
                // console.error(`Path ${JSON.stringify(expression)} evaluated directly did not resolve to a single number: ${JSON.stringify(value)}.`);
                return NaN;
            }
            return value;
        }
    }

    // Case 3: Expression is of an unsupported type
    // console.error(`Cannot evaluate expression of type ${typeof expression}: ${JSON.stringify(expression)}`);
    return NaN;
}
