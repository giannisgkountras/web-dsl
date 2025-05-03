import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    ResponsiveContainer
} from "recharts";
import { WebsocketContext } from "../context/WebsocketContext";
import { useWebsocket } from "../hooks/useWebsocket";
import { useContext, useState, useEffect } from "react";
import { IoReload } from "react-icons/io5";
import { getValueByPath, getNameFromPath } from "../utils/getValueByPath";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";

const CustomPieChart = ({
    topic,
    sourceOfContent,
    staticChartData = null,
    restData = null,
    dbData = null,
    valuePath,
    namePath,
    description = null
}) => {
    const [chartData, setChartData] = useState([]);
    const ws = useContext(WebsocketContext);
    const allPaths = [namePath, valuePath];
    const pathNames = allPaths.map(getNameFromPath);
    const { name, path, method, params } = restData || {};

    const fetchExternalData = async () => {
        try {
            let allData = [];
            const keys = pathNames;
            const response =
                sourceOfContent === "rest"
                    ? await proxyRestCall({ name, path, method, params })
                    : await queryDB(dbData);

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
            <ResponsiveContainer width={400} height={300}>
                <PieChart>
                    <Pie
                        dataKey={
                            sourceOfContent === "static"
                                ? valuePath
                                : pathNames[1]
                        }
                        nameKey={
                            sourceOfContent === "static"
                                ? namePath
                                : pathNames[0]
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
                        {chartData.map((_, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={colors[index % colors.length]}
                            />
                        ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};

export default CustomPieChart;
