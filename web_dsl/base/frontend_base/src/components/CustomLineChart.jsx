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

const CustomLineChart = ({ topic, attributes, xLabel, yLabel }) => {
    // Generate initial data dynamically based on attributes
    const initialData = attributes.reduce((acc, attr) => {
        acc[attr.name] = "0";
        return acc;
    }, {});

    const [chartData, setChartData] = useState([initialData]);
    const ws = useContext(WebsocketContext);

    // Handle WebSocket messages
    useWebsocket(ws, topic, (msg) => {
        let newData = {};
        attributes.forEach((attr) => {
            newData[attr.name] = convertTypeValue(msg[attr.name], attr.type);
        });
        setChartData((prevData) => [...prevData, newData]);
    });

    // Define an array of colors for the lines
    const colors = ["#fabd2f", "#d3869b", "#83a598", "#8ec07c", "#fe8019"];

    // Ensure there are at least two attributes: one for X-axis and one for Y-axis
    if (attributes.length < 2) {
        return (
            <div>
                Error: At least two attributes are required for the chart.
            </div>
        );
    }

    const xDataKey = attributes[0].name; // First attribute for X-axis
    const lineAttributes = attributes.slice(1); // Remaining attributes for lines

    return (
        <LineChart data={chartData} width={500} height={300}>
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
                    key={attr.name}
                    isAnimationActive={false}
                    type="monotone"
                    dataKey={attr.name}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={{ fill: colors[index % colors.length] }}
                />
            ))}
        </LineChart>
    );
};

export default CustomLineChart;
