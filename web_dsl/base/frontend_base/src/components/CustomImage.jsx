import placeholder from "../assets/placeholderimage";
import { getValueByPath } from "../utils/getValueByPath";

const CustomImage = ({
    entityData,
    width,
    height,
    sourceOfContent,
    sourceStatic,
    contentPath,
    repetitionItem = null
}) => {
    const frame = getValueByPath(entityData, contentPath) || placeholder;

    return (
        <div className="w-fit h-fit relative">
            {sourceOfContent === "rest" ||
            sourceOfContent === "broker" ||
            sourceOfContent === "db" ? (
                <img
                    style={{
                        width: `${width ? width : 400}px`,
                        height: `${height ? height : 400}px`
                    }}
                    src={frame}
                ></img>
            ) : (
                <img
                    style={{
                        width: `${width ? width : 400}px`,
                        height: `${height ? height : 400}px`
                    }}
                    src={
                        typeof repetitionItem === "string"
                            ? repetitionItem
                            : sourceStatic
                    }
                ></img>
            )}
        </div>
    );
};

export default CustomImage;
