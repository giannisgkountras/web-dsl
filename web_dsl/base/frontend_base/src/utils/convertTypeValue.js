const convertTypeValue = (value, type) => {
    switch (type) {
        case "IntAttribute":
            return parseInt(value);
        case "FloatAttribute":
            return parseFloat(value);
        case "BoolAttribute":
            return value === "true" || value === true;
        default:
            return value;
    }
};

export default convertTypeValue;
