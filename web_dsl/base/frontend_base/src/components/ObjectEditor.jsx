import { useState } from "react";
import { IoMdAddCircleOutline } from "react-icons/io";
import { RiDeleteBin5Fill } from "react-icons/ri";

const ObjectEditor = ({ initialData, onChange }) => {
    const [data, setData] = useState(initialData || {});

    // Handle key change
    const handleKeyChange = (oldKey, newKey) => {
        if (!newKey || newKey in data) return; // Prevent duplicates or empty keys
        const updatedData = { ...data };
        updatedData[newKey] = updatedData[oldKey];
        delete updatedData[oldKey];
        setData(updatedData);
        onChange(updatedData);
    };

    // Handle value change
    const handleValueChange = (key, value) => {
        const updatedData = { ...data, [key]: value };
        setData(updatedData);
        onChange(updatedData);
    };

    // Handle adding a new field
    const addField = () => {
        const newKey = `key${Object.keys(data).length + 1}`; // Generate unique key
        setData({ ...data, [newKey]: "" });
        onChange({ ...data, [newKey]: "" });
    };

    // Handle deleting a field
    const deleteField = (key) => {
        const updatedData = { ...data };
        delete updatedData[key];
        setData(updatedData);
        onChange(updatedData);
    };

    // Handle Enter key press to add a new field
    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            addField();
        }
    };

    return (
        <div className="p-4  w-full max-w-md flex justify-center items-center flex-col">
            <h2 className="mb-2">Edit JSON to send</h2>
            {Object.entries(data).map(([key, value]) => (
                <div key={key} className="flex items-center mb-2">
                    {/* Editable Key */}
                    <input
                        type="text"
                        defaultValue={key}
                        onBlur={(e) => handleKeyChange(key, e.target.value)}
                        className="p-1 border rounded w-1/2 font-mono text-sm"
                    />
                    <span className="mx-2">:</span>
                    {/* Editable Value */}
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => handleValueChange(key, e.target.value)}
                        className="p-1 border rounded w-1/2"
                        onKeyDown={handleKeyDown}
                    />
                    {/* Delete Button */}
                    <button
                        onClick={() => deleteField(key)}
                        className="ml-2 text-red-500 cursor-pointer"
                    >
                        <RiDeleteBin5Fill className="text-xl" />
                    </button>
                </div>
            ))}
            <button
                onClick={addField}
                className="mt-2 p-2 cursor-pointer bg-[#076678]  text-white rounded flex items-center "
            >
                <IoMdAddCircleOutline className="text-xl mr-1" /> Add
            </button>
        </div>
    );
};

export default ObjectEditor;
