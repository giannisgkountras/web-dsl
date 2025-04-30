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
import { useContext, useState, useEffect } from "react";
import { IoReload } from "react-icons/io5";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";

const CustomLineChart = ({
    topic,
    xLabel,
    yLabel,
    sourceOfContent,
    xValue = null,
    yValues = [],
    staticChartData = null,
    restData = null,
    dbData = null
}) => {
    const [chartData, setChartData] = useState([]);
    const ws = useContext(WebsocketContext);
    const allPaths = [xValue, ...yValues];
    const { name, path, method, params } = restData || {};
    const pathNames = allPaths.map(getNameFromPath);
    // Fetch and transform data from REST or DB
    const fetchExternalData = async () => {
        try {
            // 1. get the raw response (could be an array, or nested under contentPath)
            const response =
                sourceOfContent === "rest"
                    ? await proxyRestCall({ name, path, method, params })
                    : await queryDB(dbData);

            // 3. map over each object to build chartData entries
            const formattedData = response.map((item) => {
                const point = {};
                allPaths.forEach((path, index) => {
                    point[pathNames[index]] = getValueByPath(item, path);
                });
                return point;
            });

            console.log(formattedData);

            // 4. set the *whole* array as your chartData
            setChartData(formattedData);
        } catch (err) {
            console.error("Failed to fetch chart data:", err);
            toast.error("Failed to load chart data");
        }
    };

    // WebSocket handler
    useWebsocket(sourceOfContent === "broker" ? ws : null, topic, (msg) => {
        try {
            const newData = {};
            allPaths.forEach((path, index) => {
                newData[pathNames[index]] = getValueByPath(msg, path);
            });
            setChartData((prevData) => [...prevData, newData]);
        } catch (error) {
            toast.error("Error updating chart from WebSocket");
            console.error("WebSocket error:", error);
        }
    });

    useEffect(() => {
        if (sourceOfContent === "rest" || sourceOfContent === "db") {
            fetchExternalData();
        }
    }, []);

    const xDataKey = sourceOfContent === "static" ? xValue : pathNames[0];
    const lineDataKeys = pathNames.slice(1);
    const colors = ["#fabd2f", "#d3869b", "#83a598", "#8ec07c", "#fe8019"];

    return (
        <div className="relative p-6">
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    onClick={fetchExternalData}
                    className="absolute top-0 right-0 p-2 text-white hover:text-gray-400 cursor-pointer"
                    title="Reload chart data"
                >
                    <IoReload size={20} />
                </button>
            )}
            <LineChart
                data={
                    sourceOfContent === "static" ? staticChartData : chartData
                }
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
        </div>
    );
};

export default CustomLineChart;
