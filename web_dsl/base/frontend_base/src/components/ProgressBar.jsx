import { getValueByPath } from "../utils/getValueByPath";

const ProgressBar = ({
    entityData,
    sourceOfContent,
    staticValue,
    contentPath,
    max,
    maxStatic = 0,
    description,
    barColor = "#80A499",
    textColor = "#fff",
    trackColor = "#3c544c"
}) => {
    let currentValue = 0;
    let maxValue = 0;
    if (sourceOfContent === "static") {
        currentValue = staticValue || 0;
    } else {
        currentValue = getValueByPath(entityData, contentPath) || 0;
    }
    if (maxStatic === 0) {
        maxValue = getValueByPath(entityData, max) || 0;
    } else {
        maxValue = maxStatic;
    }

    const percentage = Math.min((currentValue / maxValue) * 100, 100);
    return (
        <div className="w-full flex flex-col justify-center items-center relative">
            <div className="w-2/3">
                {description && (
                    <div className="mb-1 text-sm font-medium">
                        {description}
                    </div>
                )}
                <div
                    className="w-full rounded-full h-4 overflow-hidden"
                    style={{ backgroundColor: trackColor }}
                >
                    <div
                        className="h-full transition-all duration-500"
                        style={{
                            width: `${percentage}%`,
                            backgroundColor: barColor
                        }}
                    ></div>
                </div>
                <div
                    className="mt-1 text-xs text-right"
                    style={{ color: textColor }}
                >
                    {Math.round(percentage)}%
                </div>
            </div>
        </div>
    );
};

export default ProgressBar;
