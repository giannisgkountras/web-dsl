import React, { useState } from "react";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";

const CustomForm = ({ elements, restData, description }) => {
    // Track form field values by index
    const [formData, setFormData] = useState({});

    // Handle input changes
    const handleChange = (datakey) => (e) => {
        const key = datakey;
        const value = e.target.value;

        setFormData((prev) => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await proxyRestCall({
                ...restData,
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }
            console.log("Success:", response);
        } catch (error) {
            console.error("Submission failed:", error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h1 className="text-lg w-full text-center">{description}</h1>
            {elements.map((el, idx) => {
                if (el.kind === "label") {
                    return <label key={idx}>{el.content}</label>;
                }

                // Otherwise treat as input
                return (
                    <input
                        key={el.datakey}
                        type={el.type}
                        placeholder={el.placeholder}
                        required={el.required}
                        onChange={handleChange(el.datakey)}
                    />
                );
            })}
            <button className="btn hover:cursor-pointer" type="submit">
                Submit
            </button>
        </form>
    );
};

export default CustomForm;
