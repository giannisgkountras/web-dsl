import { CartesianGrid, BarChart, Bar, Tooltip, XAxis, YAxis } from "recharts";
import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useState, useEffect } from "react";
import { IoReload } from "react-icons/io5";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";

const CustomBarChart = ({
    topic,
    xLabel,
    yLabel,
    sourceOfContent,
    xValue = null,
    yValues = [],
    staticChartData = null,
    restData = null,
    dbData = null,
    description = null
}) => {
    const [chartData, setChartData] = useState([]);
    const ws = useContext(WebsocketContext);
    const allPaths = [xValue, ...yValues];
    const { name, path, method, params } = restData || {};
    const pathNames = allPaths.map(getNameFromPath);

    const fetchExternalData = async () => {
        try {
            let allData = [];
            const keys = pathNames;
            const response =
                sourceOfContent === "rest"
                    ? await proxyRestCall({ name, path, method, params })
                    : await queryDB(dbData);
            console.log(response);

            for (const dataPath of allPaths) {
                const data = getValueByPath(response, dataPath);
                if (data) {
                    allData.push(data);
                }
            }

            const combinedData = allData[0].map((_, i) => {
                const obj = {};
                keys.forEach((key, j) => {
                    obj[key] = allData[j][i];
                });
                return obj;
            });

            setChartData(combinedData);
        } catch (err) {
            console.error("Failed to fetch chart data:", err);
            toast.error("Failed to load chart data");
        }
    };

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
        if (sourceOfContent === "static") {
            setChartData(staticChartData);
        }
    }, []);

    const xDataKey = sourceOfContent === "static" ? xValue : pathNames[0];
    const barDataKeys =
        sourceOfContent === "static" ? yValues : pathNames.slice(1);
    const colors = ["#fabd2f", "#d3869b", "#83a598", "#8ec07c", "#fe8019"];

    return (
        <div className="relative p-6">
            {description && (
                <h1 className="text-lg w-full text-center">{description}</h1>
            )}
            {(sourceOfContent === "rest" || sourceOfContent === "db") && (
                <button
                    onClick={fetchExternalData}
                    className="absolute top-0 right-0 p-2 text-white hover:text-gray-400 cursor-pointer"
                    title="Reload chart data"
                >
                    <IoReload size={20} />
                </button>
            )}
            <BarChart
                data={
                    sourceOfContent === "static" ? staticChartData : chartData
                }
                width={500}
                height={300}
                style={{
                    backgroundColor: "#13191e",
                    borderRadius: "15px",
                    padding: "0.5rem"
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
                {barDataKeys.map((key, index) => (
                    <Bar
                        key={key}
                        dataKey={key}
                        fill={colors[index % colors.length]}
                        barSize={25}
                        isAnimationActive={false}
                    />
                ))}
            </BarChart>
        </div>
    );
};

export default CustomBarChart;
