import { useEffect, useMemo, useState } from "react";
import convertTypeValue from "../utils/convertTypeValue";
import { FaEdit, FaTrash, FaSave } from "react-icons/fa";
import { getNameFromPath, getValueByPath } from "../utils/getValueByPath";
import {
    objectOfListsToListOfObjects,
    isObjectOfLists
} from "../utils/transformations";
import { modifyDB } from "../api/dbModify";
import CustomCheckbox from "./CustomCheckbox";

const Table = ({
    entityData,
    attributes = [],
    dbData = {},
    sourceOfContent,
    dbType,
    primaryKey,
    table,
    description,
    crud = "false"
}) => {
    const extendedAttributes = [[primaryKey], ...attributes];
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState([]);
    const [editingPkValue, setEditingPkValue] = useState(null);
    const [newRecord, setNewRecord] = useState({});

    // Determine if CRUD operations are enabled
    const isCrudEnabled = crud === true || crud === "true";

    const columns = useMemo(() => {
        if (!data || data.length === 0 || data?.status === "error") return [];
        return Object.keys(data[0]);
    }, [data]);

    const emptyRecord = useMemo(() => {
        if (!data || data.length === 0 || data?.status === "error") return {};
        const rec = {};
        columns.forEach((col) => {
            if (col !== primaryKey) {
                rec[col] = typeof data[0]?.[col] === "boolean" ? false : "";
            }
        });
        return rec;
    }, [columns, primaryKey, data]);

    useEffect(() => {
        setNewRecord(emptyRecord);
    }, [emptyRecord]);

    const reloadValue = async () => {
        setLoading(true);
        let response = entityData;

        let listData = isObjectOfLists(response)
            ? objectOfListsToListOfObjects(response)
            : response;

        if (extendedAttributes.length <= 1) {
            setData(listData);
        } else {
            const processedData = Array.isArray(listData)
                ? listData.map((item, index) => {
                      const newItem = {};
                      extendedAttributes.forEach((attribute) => {
                          try {
                              const value = getValueByPath(item, attribute);
                              const name = getNameFromPath(attribute);
                              newItem[name] = value;
                          } catch (error) {
                              console.error(
                                  `Error extracting attribute "${attribute}" at index ${index}: ${error.message}`
                              );
                              newItem[attribute] = null; // or undefined, "", or skip it
                          }
                      });
                      return newItem;
                  })
                : [];
            setData(processedData);
        }
        setLoading(false);
    };

    useEffect(() => {
        if (!entityData) return;
        reloadValue();
    }, [entityData]);

    const handleChange = (pkValue, col, rawValue) => {
        if (!isCrudEnabled) return;
        const value = convertTypeValue(rawValue, typeof data[0][col]);
        setData((rows) =>
            rows.map((r) =>
                r[primaryKey] === pkValue ? { ...r, [col]: value } : r
            )
        );
    };

    const handleNewChange = (col, rawValue) => {
        if (!isCrudEnabled) return;
        const value = convertTypeValue(rawValue, typeof newRecord[col]);
        setNewRecord((r) => ({ ...r, [col]: value }));
    };

    const handleSave = async (pkValue) => {
        if (!isCrudEnabled) return;
        const item = data.find((r) => r[primaryKey] === pkValue);
        if (!item) return;

        if (sourceOfContent === "db") {
            if (dbType === "mysql") {
                const setClause = columns
                    .filter((col) => col !== primaryKey)
                    .map((col) => `${col} = '${item[col]}'`)
                    .join(", ");
                const query = `UPDATE ${table} SET ${setClause} WHERE ${primaryKey} = '${item[primaryKey]}'`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query,
                    dbType: dbType
                });
            } else if (dbType === "mongo") {
                const updateData = { ...item };
                delete updateData[primaryKey];
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    collection: dbData.collection,
                    modification: "update",
                    filter: { [primaryKey]: item[primaryKey] },
                    new_data: updateData,
                    dbType: dbType
                });
            }
        }
        setEditingPkValue(null);
    };

    const handleDelete = async (pkValue) => {
        if (!isCrudEnabled) return;
        if (sourceOfContent === "db") {
            if (dbType === "mysql") {
                const query = `DELETE FROM ${table} WHERE ${primaryKey} = '${pkValue}'`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query,
                    dbType: dbType
                });
            } else if (dbType === "mongo") {
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    collection: dbData.collection,
                    modification: "delete",
                    filter: { [primaryKey]: pkValue },
                    dbType: dbType
                });
            }
        }
        setData((rows) => rows.filter((r) => r[primaryKey] !== pkValue));
    };

    const handleAdd = async () => {
        if (!isCrudEnabled) return;
        if (sourceOfContent === "db") {
            if (dbType === "mysql") {
                const columnsToInsert = columns.filter(
                    (col) => col !== primaryKey
                );
                const values = columnsToInsert.map(
                    (col) => `'${newRecord[col]}'`
                );
                const query = `INSERT INTO ${table} (${columnsToInsert.join(
                    ", "
                )}) VALUES (${values.join(", ")})`;
                await modifyDB({
                    connection_name: dbData.connection_name,
                    database: dbData.database,
                    query: query,
                    dbType: dbType
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
                    new_data: newData,
                    dbType: dbType
                });
                await reloadValue();
            }
        }
        setNewRecord(emptyRecord);
    };

    const capitalize = (s) => s[0].toUpperCase() + s.slice(1);

    if (loading || !columns.length) {
        return (
            <div className="flex justify-center items-center w-full h-64 text-white">
                <p className="animate-pulse">Loading table data...</p>
            </div>
        );
    }
    return (
        <div className="flex flex-col text-white justify-start items-center w-full h-fit max-h-96 bg-[#13191E] rounded-2xl">
            {/* Header */}
            <h1 className="p-4 text-lg font-semibold">{description}</h1>
            <div className="w-full sticky top-0 z-10 bg-[#13191E] border-b border-[#313641] p-4">
                <div
                    className="grid gap-2 font-bold"
                    style={{
                        gridTemplateColumns: `repeat(${
                            columns.length + (isCrudEnabled ? 1 : 0)
                        }, minmax(100px,1fr))`
                    }}
                >
                    {columns.length > 0 &&
                        columns.map((col) => (
                            <div key={col} className="text-left">
                                {capitalize(col)}
                            </div>
                        ))}
                    {isCrudEnabled && (
                        <div className="text-center">Actions</div>
                    )}
                </div>
            </div>

            {/* Body */}
            <div className="w-full max-h-80 overflow-y-auto">
                {data.length > 0 &&
                    data.map((row) => (
                        <div
                            key={row[primaryKey]}
                            className="grid w-full gap-2 p-2 border-b border-[#313641] items-center"
                            style={{
                                gridTemplateColumns: `repeat(${
                                    columns.length + (isCrudEnabled ? 1 : 0)
                                }, minmax(0, 1fr))`
                            }}
                        >
                            {columns.length > 0 &&
                                columns.map((col) => {
                                    const value = row[col];

                                    return (
                                        <div
                                            key={col}
                                            className="overflow-hidden text-ellipsis whitespace-nowrap cursor-pointer"
                                            title={String(value ?? "-")}
                                        >
                                            {col === primaryKey ||
                                            editingPkValue !==
                                                row[primaryKey] ? (
                                                typeof value === "boolean" ? (
                                                    <CustomCheckbox
                                                        checked={value}
                                                        disabled={true}
                                                    />
                                                ) : (
                                                    <p className="text-left px-2 text-ellipsis whitespace-nowrap overflow-hidden">
                                                        {value ?? "-"}
                                                    </p>
                                                )
                                            ) : typeof value === "boolean" ? (
                                                <CustomCheckbox
                                                    checked={value}
                                                    onChange={(e) =>
                                                        handleChange(
                                                            row[primaryKey],
                                                            col,
                                                            e.target.checked
                                                        )
                                                    }
                                                />
                                            ) : (
                                                <input
                                                    className="bg-transparent w-full text-white focus:outline-none border-b border-transparent focus:border-white px-2"
                                                    value={value}
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
                                    );
                                })}
                            {isCrudEnabled && (
                                <div className="flex justify-center space-x-2">
                                    {editingPkValue === row[primaryKey] ? (
                                        <button
                                            onClick={() =>
                                                handleSave(row[primaryKey])
                                            }
                                            className="p-2 rounded-full hover:bg-[#03C64C]/20 cursor-pointer"
                                        >
                                            <FaSave className="text-[#03C64C]" />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() =>
                                                setEditingPkValue(
                                                    row[primaryKey]
                                                )
                                            }
                                            className="p-2 rounded-full hover:bg-[#2D4272]/20 cursor-pointer"
                                        >
                                            <FaEdit className="text-white" />
                                        </button>
                                    )}
                                    <button
                                        onClick={() =>
                                            handleDelete(row[primaryKey])
                                        }
                                        className="p-2 rounded-full hover:bg-[#FA2C37]/20 cursor-pointer"
                                    >
                                        <FaTrash className="text-[#FA2C37]" />
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}

                {/* New Record Row */}
                {isCrudEnabled && (
                    <div
                        className="grid gap-2 p-2 bg-[#13191E] rounded-b-2xl"
                        style={{
                            gridTemplateColumns: `repeat(${
                                columns.length + 1
                            }, minmax(100px,1fr))`
                        }}
                    >
                        {columns.length > 0 &&
                            columns.map((col) => {
                                const value = newRecord[col];

                                if (col === primaryKey)
                                    return <div key={col} />;

                                return typeof value === "boolean" ? (
                                    <div
                                        key={col}
                                        className="flex justify-center items-center"
                                    >
                                        <CustomCheckbox
                                            checked={value}
                                            onChange={(e) =>
                                                handleNewChange(
                                                    col,
                                                    e.target.checked
                                                )
                                            }
                                        />
                                    </div>
                                ) : (
                                    <input
                                        key={col}
                                        className="p-1 bg-transparent text-white focus:outline-none border-b border-transparent focus:border-white px-2 placeholder-gray-400"
                                        placeholder={capitalize(col)}
                                        value={value}
                                        onChange={(e) =>
                                            handleNewChange(col, e.target.value)
                                        }
                                    />
                                );
                            })}
                        <button
                            onClick={handleAdd}
                            className="bg-[#2D4272] px-3 py-1 rounded-md font-medium hover:bg-[#253A66] cursor-pointer"
                        >
                            Add
                        </button>
                    </div>
                )}
                {!isCrudEnabled && (
                    <div className="w-full h-4 rounded-b-2xl"></div>
                )}
            </div>
        </div>
    );
};

export default Table;
