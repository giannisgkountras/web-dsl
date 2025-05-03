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
