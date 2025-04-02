import { useState, useRef } from "react";
import Editor from "react-simple-code-editor";
import { highlight, languages } from "prismjs/components/prism-core";
import "prismjs/components/prism-json";
import "prismjs/themes/prism-dark.css";

const ObjectEditor = ({ initialData, onChange, jsonError, setJsonError }) => {
    const [jsonText, setJsonText] = useState(
        JSON.stringify(initialData, null, 2)
    );
    const editorRef = useRef(null);

    // Auto-closing pairs
    const pairs = {
        "{": "}",
        "[": "]",
        '"': '"'
    };

    // Handle key presses for auto-closing
    const handleKeyDown = (e) => {
        const { key, target } = e;
        if (pairs[key]) {
            e.preventDefault();
            const start = target.selectionStart;
            const end = target.selectionEnd;
            const value = target.value;
            const before = value.substring(0, start);
            const after = value.substring(end);
            const closingChar = pairs[key];
            const newValue = before + key + closingChar + after;

            setJsonText(newValue);
            // Use setTimeout to ensure cursor is set after state update
            setTimeout(() => {
                target.selectionStart = start + 1;
                target.selectionEnd = start + 1;
            }, 0);
        }
    };

    // Handle JSON changes
    const handleJsonChange = (code) => {
        setJsonText(code);
        try {
            const parsed = JSON.parse(code);
            setJsonError(null);
            onChange(parsed);
        } catch (err) {
            setJsonError("Invalid JSON");
        }
    };

    return (
        <div className="p-4 w-full max-w-lg flex flex-col">
            <h2 className="mb-2 text-lg font-semibold text-gray-200">
                Edit JSON
            </h2>
            <Editor
                ref={editorRef}
                value={jsonText}
                onValueChange={handleJsonChange}
                onKeyDown={handleKeyDown} // Add auto-closing logic
                highlight={(code) => highlight(code, languages.json, "json")}
                padding={10}
                style={{
                    fontFamily: "monospace",
                    fontSize: "14px",
                    backgroundColor: "#101828",
                    color: "#ffffff", // Ensure text is visible on dark background
                    border: "1px solid #2d4373",
                    borderRadius: "0.5rem",
                    minHeight: "200px", // Minimum height for better usability
                    outline: "none" // Remove default focus outline
                }}
                textareaClassName="focus:ring-2 focus:ring-blue-500" // Add focus ring to the underlying textarea
            />

            {!jsonError && <p className="text-green-500 mt-1">Valid JSON</p>}
            {jsonError && <p className="text-red-500 mt-1">{jsonError}</p>}
        </div>
    );
};

export default ObjectEditor;
