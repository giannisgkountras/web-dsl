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
import convertTypeValue from "../utils/convertTypeValue";

const CustomLineChart = ({
    topic,
    attributes,
    xLabel,
    yLabel,
    sourceOfContent,
    xValue = null,
    yValues = null,
    staticChartData = null
}) => {
    // Generate initial data dynamically based on attributes
    const initialData = attributes.reduce((acc, attr) => {
        acc[attr.name] = "0";
        return acc;
    }, {});

    const [chartData, setChartData] = useState([initialData]);
    const ws = useContext(WebsocketContext);

    // Handle WebSocket messages
    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        let newData = {};
        attributes.forEach((attr) => {
            newData[attr.name] = convertTypeValue(msg[attr.name], attr.type);
        });
        setChartData((prevData) => [...prevData, newData]);
    });

    // Define an array of colors for the lines
    const colors = ["#fabd2f", "#d3869b", "#83a598", "#8ec07c", "#fe8019"];

    const xDataKey = sourceOfContent === "static" ? xValue : attributes[0].name; // First attribute for X-axis or X-value if static content
    const lineAttributes =
        sourceOfContent === "static" ? yValues : attributes.slice(1); // Remaining attributes for lines or Y-values if static content

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

            {/* Generate a <Line> for each attribute beyond the first */}
            {lineAttributes.map((attr, index) => (
                <Line
                    key={attr.name || attr} // Use attr.name or attr if static for the key
                    isAnimationActive={false}
                    type="monotone"
                    dataKey={attr.name || attr} // Use attr.name or attr if static for the key
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={{ fill: colors[index % colors.length] }}
                />
            ))}
        </LineChart>
    );
};

export default CustomLineChart;
