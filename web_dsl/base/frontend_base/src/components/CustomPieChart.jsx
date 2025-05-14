import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { WebsocketContext } from "../context/WebsocketContext";
import { useContext, useState, useEffect } from "react";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";
import { colors } from "../lib/colors";
import { transformToArrayOfObjects } from "../utils/transformations";

const CustomPieChart = ({
    entityData,
    sourceOfContent,
    staticChartData = null,
    valuePath,
    namePath,
    description = null
}) => {
    const [chartData, setChartData] = useState([]);
    const allPaths = [namePath, valuePath];
    const pathNames = allPaths.map(getNameFromPath);

    useEffect(() => {
        if (!entityData) {
            return;
        }
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
            setChartData(newData);
        } else if (sourceOfContent === "static") {
            setChartData(staticChartData);
        }
    }, [entityData]);

    return (
        <div className="relative w-full h-full flex flex-col items-center justify-center">
            {description && (
                <h1 className="text-lg w-full text-center mb-2 font-semibold">
                    {description}
                </h1>
            )}

            <PieChart
                width={450}
                height={350}
                style={{
                    backgroundColor: "#13191e",
                    borderRadius: "15px",
                    position: "relative"
                }}
            >
                <Pie
                    dataKey={
                        sourceOfContent === "static" ? valuePath : pathNames[1]
                    }
                    nameKey={
                        sourceOfContent === "static" ? namePath : pathNames[0]
                    }
                    data={
                        sourceOfContent === "static"
                            ? staticChartData
                            : chartData
                    }
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    label
                >
                    {Array.isArray(chartData) &&
                        chartData.map((_, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={colors[index % colors.length]}
                            />
                        ))}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </div>
    );
};

export default CustomPieChart;
