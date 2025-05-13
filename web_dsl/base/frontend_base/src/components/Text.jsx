import { getValueByPath } from "../utils/getValueByPath";

const Text = ({
    entityData,
    contentPath,
    size = 18,
    color,
    weight = 400,
    staticContent,
    sourceOfContent,
    repetitionItem = null
}) => {
    const content = getValueByPath(entityData, contentPath);

    return (
        <h1
            style={{
                ...(size !== 0 && { fontSize: `${size}px` }),
                color: color,
                fontWeight: weight
            }}
            className="text-center"
        >
            {typeof repetitionItem === "string" ||
            typeof repetitionItem === "number"
                ? repetitionItem
                : sourceOfContent === "static" || sourceOfContent === ""
                ? staticContent
                : content}
        </h1>
    );
};

export default Text;
