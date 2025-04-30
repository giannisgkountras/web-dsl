import {
    CartesianGrid,
    Line,
    LineChart,
    Tooltip,
    XAxis,
    YAxis
} from "recharts";
import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useState } from "react";

const getValueByPath = (obj, path) => {
    return path.reduce((acc, key) => acc?.[key], obj);
};

const CustomLineChart = ({
    topic,
    xLabel,
    yLabel,
    sourceOfContent,
    xValue = null,
    yValues = [],
    staticChartData = null
}) => {
    const [chartData, setChartData] = useState([]);
    const ws = useContext(WebsocketContext);

    const allData = [xValue, ...yValues]; // Each item is a path array like ['data', 1, 'temperature']

    // Handle WebSocket messages
    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const newData = {};
            allData.forEach((path, index) => {
                newData[`value${index}`] = getValueByPath(msg, path);
            });
            setChartData((prevData) => [...prevData, newData]);
        } catch (error) {
            console.error("Error processing WebSocket message:", error);
        }
    });

    // Define an array of colors for the lines
    const colors = ["#fabd2f", "#d3869b", "#83a598", "#8ec07c", "#fe8019"];

    const xDataKey = sourceOfContent === "static" ? xValue : "value0"; // value0 corresponds to xValue path
    const lineDataKeys = yValues.map((_, index) => `value${index + 1}`); // yValues mapped to value1, value2, ...

    return (
        <LineChart
            data={sourceOfContent === "static" ? staticChartData : chartData}
            width={500}
            height={300}
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
                    dx: -10
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
        </LineChart>
    );
};

export default CustomLineChart;
