import { GaugeComponent } from "react-gauge-component";
import { getValueByPath } from "../utils/getValueByPath";

const Gauge = ({
    entityData = null,
    sourceOfContent,
    staticValue,
    contentPath,
    description = null,
    repetitionItem = null
}) => {
    const value = getValueByPath(entityData, contentPath);

    return (
        <div className="flex flex-col justify-center items-center relative">
            {typeof repetitionItem === "string" ||
            typeof repetitionItem === "number" ? (
                <GaugeComponent value={repetitionItem} />
            ) : sourceOfContent === "static" || sourceOfContent === "" ? (
                <GaugeComponent value={staticValue} />
            ) : (
                <GaugeComponent value={value} />
            )}
            {description && <h1 className="text-lg">{description}</h1>}
        </div>
    );
};

export default Gauge;
