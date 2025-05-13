import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    Tooltip,
    XAxis,
    YAxis
} from "recharts";
import { useState, useEffect } from "react";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";
import { colors } from "../lib/colors";
import { transformToArrayOfObjects } from "../utils/transformations";

const CustomLineChart = ({
    entityData,
    xLabel,
    yLabel,
    sourceOfContent,
    xValue = null,
    yValues = [],
    staticChartData = null,
    description = null
}) => {
    const [chartData, setChartData] = useState([]);
    const allPaths = [xValue, ...yValues];
    const pathNames = allPaths.map(getNameFromPath);

    useEffect(() => {
        if (sourceOfContent === "rest" || sourceOfContent === "db") {
            const transformed = transformToArrayOfObjects(
                entityData,
                allPaths,
                pathNames
            );
            setChartData(transformed);
        } else if (sourceOfContent === "broker") {
            const newData = {};
            allPaths.forEach((path, index) => {
                newData[pathNames[index]] = getValueByPath(entityData, path);
            });
            setChartData((prevData) => [...prevData, newData]);
        } else if (sourceOfContent === "static") {
            setChartData(staticChartData);
        }
    }, [entityData]);

    const xDataKey = sourceOfContent === "static" ? xValue : pathNames[0];
    const lineDataKeys =
        sourceOfContent === "static" ? yValues : pathNames.slice(1);

    return (
        <div className="relative w-full h-full flex flex-col items-center justify-center">
            {description && (
                <h1 className="text-lg w-full text-center mb-2 font-semibold">
                    {description}
                </h1>
            )}

            <LineChart
                data={
                    sourceOfContent === "static" ? staticChartData : chartData
                }
                width={450}
                height={350}
                style={{
                    backgroundColor: "#13191e",
                    borderRadius: "15px",
                    position: "relative",
                    padding: "1rem"
                }}
            >
                <CartesianGrid stroke="#3c3836" strokeDasharray="3 3" />
                <XAxis
                    dataKey={xDataKey}
                    stroke="#fff"
                    label={{
                        value: xLabel,
                        position: "insideBottom",
                        offset: -5,
                        fill: "#fff"
                    }}
                />
                <YAxis
                    stroke="#fff"
                    label={{
                        value: yLabel,
                        position: "outsideLeft",
                        fill: "#fff",
                        angle: -90,
                        dx: -35
                    }}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: "#282828",
                        border: "none",
                        color: "#fff",
                        borderRadius: "10px"
                    }}
                    itemStyle={{ color: "#fff" }}
                />
                {lineDataKeys.map((key, index) => (
                    <Line
                        key={key}
                        isAnimationActive={false}
                        type="monotone"
                        dataKey={key}
                        stroke={colors[index % colors.length]}
                        strokeWidth={2}
                        dot={{ fill: colors[index % colors.length] }}
                    />
                ))}
                <Legend />
            </LineChart>
        </div>
    );
};

export default CustomLineChart;
