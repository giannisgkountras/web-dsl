import React, { useEffect, useMemo, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";
import { proxyRestCall } from "../api/proxyRestCall";
import { queryDB } from "../api/dbQuery";
import { FaEdit, FaTrash, FaSave } from "react-icons/fa";
import { getNameFromPath, getValueByPath } from "../utils/getValueByPath";
import {
    objectOfListsToListOfObjects,
    isObjectOfLists
} from "../utils/transformations";
import { modifyDB } from "../api/dbModify";

const CrudTable = ({
    attributes = [],
    restData = {},
    dbData = {},
    sourceOfContent,
    dbType,
    primaryKey
}) => {
    const [data, setData] = useState([]);
    const [editingPkValue, setEditingPkValue] = useState(null);
    const [newRecord, setNewRecord] = useState({});

    const columns = useMemo(() => {
        if (!data || data.length === 0) return [];
        return Object.keys(data[0]);
    }, [data]);

    const emptyRecord = useMemo(() => {
        const rec = {};
        columns.forEach((col) => {
            if (col !== primaryKey) {
                rec[col] = "";
            }
        });
        return rec;
    }, [columns, primaryKey]);

    useEffect(() => {
        setNewRecord(emptyRecord);
    }, [emptyRecord]);

    const reloadValue = async () => {
        let response;

        if (sourceOfContent === "rest") {
            response = await proxyRestCall(restData);
        } else if (sourceOfContent === "db") {
            response = await queryDB(dbData);
        } else {
            return;
        }

        let listData = isObjectOfLists(response)
            ? objectOfListsToListOfObjects(response)
            : response;

        if (attributes.length === 0) {
            setData(listData);
        } else {
            const processedData = listData.map((item) => {
                const newItem = {};
                attributes.forEach((attribute) => {
                    try {
                        const value = getValueByPath(item, attribute);
                        const name = getNameFromPath(attribute);
                        newItem[name] = value;
                    } catch (error) {
                        console.error(
                            "Error extracting attribute: " + error.message
                        );
                    }
                });
                return newItem;
            });
            setData(processedData);
        }
    };

    useEffect(() => {
        reloadValue();
    }, []);

    const handleChange = (pkValue, col, rawValue) => {
        const value = convertTypeValue(rawValue, typeof data[0][col]);
        setData((rows) =>
            rows.map((r) =>
                r[primaryKey] === pkValue ? { ...r, [col]: value } : r
            )
        );
    };

    const handleNewChange = (col, rawValue) => {
        const value = convertTypeValue(rawValue, typeof newRecord[col]);
        setNewRecord((r) => ({ ...r, [col]: value }));
    };

    const handleSave = async (pkValue) => {
        const item = data.find((r) => r[primaryKey] === pkValue);
        if (!item) return;

        if (sourceOfContent === "db") {
            if (dbType === "mysql") {
                const setClause = columns
                    .filter((col) => col !== primaryKey)
                    .map((col) => `${col} = '${item[col]}'`)
                    .join(", ");
                const query = `UPDATE ${dbData.collection} SET ${setClause} WHERE ${primaryKey} = '${item[primaryKey]}'`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query
                });
            } else if (dbType === "mongo") {
                const updateData = { ...item };
                delete updateData[primaryKey]; // Exclude primary key from update data
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    collection: dbData.collection,
                    modification: "update",
                    filter: { [primaryKey]: item[primaryKey] },
                    new_data: updateData
                });
            }
        }
        setEditingPkValue(null);
    };

    const handleDelete = async (pkValue) => {
        if (sourceOfTruth === "db") {
            if (dbType === "mysql") {
                const query = `DELETE FROM ${dbData.collection} WHERE ${primaryKey} = '${pkValue}'`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query
                });
            } else if (dbType === "mongo") {
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    collection: dbData.collection,
                    modification: "delete",
                    filter: { [primaryKey]: pkValue }
                });
            }
        }
        setData((rows) => rows.filter((r) => r[primaryKey] !== pkValue));
    };

    const handleAdd = async () => {
        if (sourceOfTruth === "db") {
            if (dbType === "mysql") {
                const columnsToInsert = columns.filter(
                    (col) => col !== primaryKey
                );
                const values = columnsToInsert.map(
                    (col) => `'${newRecord[col]}'`
                );
                const query = `INSERT INTO ${
                    dbData.collection
                } (${columnsToInsert.join(", ")}) VALUES (${values.join(
                    ", "
                )})`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query
                });
                await reloadValue();
            } else if (dbType === "mongo") {
                const newData = { ...newRecord };
                delete newData[primaryKey];
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    collection: dbData.collection,
                    modification: "insert",
                    new_data: newData
                });
                await reloadValue();
            }
        }
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
                        key={row[primaryKey]}
                        className="grid gap-2 p-2 bg-[#101929] border-b border-[#0D1117] items-center"
                        style={{
                            gridTemplateColumns: `repeat(${
                                columns.length + 1
                            }, minmax(100px,1fr))`
                        }}
                    >
                        {columns.map((col) => (
                            <div key={col}>
                                {col === primaryKey ||
                                editingPkValue !== row[primaryKey] ? (
                                    <p className="text-left px-2">
                                        {row[col] ?? "-"}
                                    </p>
                                ) : (
                                    <input
                                        className="bg-transparent text-white focus:outline-none border-b border-transparent focus:border-white px-2"
                                        value={row[col]}
                                        onChange={(e) =>
                                            handleChange(
                                                row[primaryKey],
                                                col,
                                                e.target.value
                                            )
                                        }
                                    />
                                )}
                            </div>
                        ))}
                        <div className="flex justify-center space-x-2">
                            {editingPkValue === row[primaryKey] ? (
                                <button
                                    onClick={() => handleSave(row[primaryKey])}
                                    className="p-2 rounded-full hover:bg-[#03C64C]/20"
                                >
                                    <FaSave className="text-[#03C64C]" />
                                </button>
                            ) : (
                                <button
                                    onClick={() =>
                                        setEditingPkValue(row[primaryKey])
                                    }
                                    className="p-2 rounded-full hover:bg-[#2D4272]/20"
                                >
                                    <FaEdit className="text-white" />
                                </button>
                            )}
                            <button
                                onClick={() => handleDelete(row[primaryKey])}
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
                    {columns.map((col) =>
                        col === primaryKey ? (
                            <div key={col} />
                        ) : (
                            <input
                                key={col}
                                className="p-1 bg-transparent text-white focus:outline-none border-b border-transparent focus:border-white px-2 placeholder-gray-400"
                                placeholder={capitalize(col)}
                                value={newRecord[col]}
                                onChange={(e) =>
                                    handleNewChange(col, e.target.value)
                                }
                            />
                        )
                    )}
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
