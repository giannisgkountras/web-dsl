import React, { useEffect, useMemo, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { FaEdit, FaTrash, FaSave } from "react-icons/fa";

const CrudTable = ({
    attributes,
    restData = {},
    dbData = {},
    sourceOfContent
}) => {
    const [data, setData] = useState([]);
    const [editingId, setEditingId] = useState(null);

    // load from REST or DB
    const reloadValue = async () => {
        if (sourceOfContent === "rest") {
            const response = await proxyRestCall(restData);
            if (attributes.length === 0) {
                setData(response);
            } else {
                const newData = response.map((item) => {
                    const newItem = {};
                    attributes.forEach((attribute) => {
                        try {
                            newItem[attribute.name] = convertTypeValue(
                                item[attribute.name],
                                attribute.type
                            );
                        } catch (error) {
                            console.error("Error converting value:", error);
                        }
                    });
                    return newItem;
                });
                setData(newData);
            }
        }
        if (sourceOfContent === "db") {
            const response = await queryDB(dbData);
            if (attributes.length === 0) {
                console.log("response", response);
                setData(response);
            } else {
                const newData = response.map((item) => {
                    const newItem = {};
                    attributes.forEach((attribute) => {
                        try {
                            newItem[attribute.name] = convertTypeValue(
                                item[attribute.name],
                                attribute.type
                            );
                        } catch (error) {
                            console.error("Error converting value:", error);
                        }
                    });
                    return newItem;
                });
                setData(newData);
            }
        }
    };

    useEffect(() => {
        reloadValue();
    }, []);

    // infer your columns from the first row of data
    const columns = useMemo(() => {
        if (!data || data.length === 0) return [];
        return Object.keys(data[0]).filter((key) => key !== "id");
    }, [data]);

    // build an “empty” record template whenever your columns change
    const emptyRecord = useMemo(() => {
        const rec = {};
        columns.forEach((col) => {
            rec[col] = "";
        });
        return rec;
    }, [columns]);

    const [newRecord, setNewRecord] = useState(emptyRecord);

    // keep newRecord in sync if columns ever change
    useEffect(() => {
        setNewRecord(emptyRecord);
    }, [emptyRecord]);

    const handleChange = (id, col, rawValue) => {
        const value = convertTypeValue(rawValue, typeof data[0][col]);
        setData((rows) =>
            rows.map((r) => (r.id === id ? { ...r, [col]: value } : r))
        );
    };

    const handleNewChange = (col, rawValue) => {
        const value = convertTypeValue(rawValue, typeof newRecord[col]);
        setNewRecord((r) => ({ ...r, [col]: value }));
    };

    const handleSave = (id) => setEditingId(null);

    const handleDelete = (id) =>
        setData((rows) => rows.filter((r) => r.id !== id));

    const handleAdd = () => {
        const nextId = data.length ? Math.max(...data.map((r) => r.id)) + 1 : 1;
        setData((rows) => [...rows, { id: nextId, ...newRecord }]);
        setNewRecord(emptyRecord);
    };

    const capitalize = (s) => s[0].toUpperCase() + s.slice(1);

    return (
        <div className="flex flex-col text-white justify-start items-center w-full h-fit max-h-96 bg-[#101929] rounded-2xl">
            {/* Header */}
            <div className="w-full sticky top-0 z-10 border-b border-[#111929] bg-[#1A2233] p-4 rounded-t-2xl">
                <div
                    className="grid gap-2 font-bold"
                    style={{
                        gridTemplateColumns: `repeat(${
                            columns.length + 1
                        }, minmax(100px,1fr))`
                    }}
                >
                    {columns.map((col) => (
                        <div key={col} className="text-left">
                            {capitalize(col)}
                        </div>
                    ))}
                    <div className="text-center">Actions</div>
                </div>
            </div>

            {/* Body */}
            <div className="w-full max-h-80 overflow-y-auto">
                {data.map((row) => (
                    <div
                        key={row.id}
                        className="grid gap-2 p-2 bg-[#101929] border-b border-[#0D1117] items-center"
                        style={{
                            gridTemplateColumns: `repeat(${
                                columns.length + 1
                            }, minmax(100px,1fr))`
                        }}
                    >
                        {columns.map((col) =>
                            editingId === row.id ? (
                                <input
                                    key={col}
                                    className="bg-transparent text-white focus:outline-none border-b border-transparent focus:border-white px-2"
                                    value={row[col]}
                                    onChange={(e) =>
                                        handleChange(
                                            row.id,
                                            col,
                                            e.target.value
                                        )
                                    }
                                />
                            ) : (
                                <p key={col} className="text-left px-2">
                                    {row[col] ?? "-"}
                                </p>
                            )
                        )}
                        <div className="flex justify-center space-x-2">
                            {editingId === row.id ? (
                                <button
                                    onClick={() => handleSave(row.id)}
                                    className="p-2 rounded-full hover:bg-[#03C64C]/20"
                                >
                                    <FaSave className="text-[#03C64C]" />
                                </button>
                            ) : (
                                <button
                                    onClick={() => setEditingId(row.id)}
                                    className="p-2 rounded-full hover:bg-[#2D4272]/20"
                                >
                                    <FaEdit className="text-white" />
                                </button>
                            )}
                            <button
                                onClick={() => handleDelete(row.id)}
                                className="p-2 rounded-full hover:bg-[#FA2C37]/20"
                            >
                                <FaTrash className="text-[#FA2C37]" />
                            </button>
                        </div>
                    </div>
                ))}

                {/* New Record Row */}
                <div
                    className="grid gap-2 p-2 bg-[#1A2233] rounded-b-2xl"
                    style={{
                        gridTemplateColumns: `repeat(${
                            columns.length + 1
                        }, minmax(100px,1fr))`
                    }}
                >
                    {columns.map((col) => (
                        <input
                            key={col}
                            className="p-1 bg-transparent text-white focus:outline-none border-b border-transparent focus:border-white px-2 placeholder-gray-400"
                            placeholder={capitalize(col)}
                            value={newRecord[col]}
                            onChange={(e) =>
                                handleNewChange(col, e.target.value)
                            }
                        />
                    ))}
                    <button
                        onClick={handleAdd}
                        className="bg-[#2D4272] px-3 py-1 rounded-md font-medium hover:bg-[#253A66]"
                    >
                        Add
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CrudTable;
