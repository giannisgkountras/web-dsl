import { useState } from "react";

const ObjectEditor = ({ initialData, onChange, jsonError, setJsonError }) => {
    const [jsonText, setJsonText] = useState(
        JSON.stringify(initialData, null, 2)
    );

    // Handle JSON changes
    const handleJsonChange = (e) => {
        const text = e.target.value;
        setJsonText(text);

        try {
            const parsed = JSON.parse(text);
            setJsonError(null); // No error
            onChange(parsed);
        } catch (err) {
            setJsonError("Invalid JSON");
        }
    };

    return (
        <div className="p-4 w-full max-w-lg flex flex-col">
            <h2 className="mb-2">Edit JSON</h2>
            <textarea
                className="w-full resize h-40 p-2 border rounded font-mono text-sm bg-gray-900"
                value={jsonText}
                onChange={handleJsonChange}
            />
            {!jsonError && <p className="text-green-500 mt-1">Valid JSON</p>}
            {jsonError && <p className="text-red-500 mt-1">{jsonError}</p>}
        </div>
    );
};

export default ObjectEditor;
