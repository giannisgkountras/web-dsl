import React, { useState } from "react";
import { toast } from "react-toastify";
import { proxyRestCall } from "../api/proxyRestCall";

const CustomForm = ({ elements, restData }) => {
    // Track form field values by index
    const [formData, setFormData] = useState({});

    // Handle input changes
    const handleChange = (index) => (e) => {
        const key = `field_${index}`;
        const value =
            e.target.type === "checkbox" || e.target.type === "radio"
                ? e.target.checked
                : e.target.value;

        setFormData((prev) => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await proxyRestCall(...restData, {
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
            {elements.map((el, idx) => {
                if (el.kind === "label") {
                    return <label key={idx}>{el.content}</label>;
                }

                // Otherwise treat as input
                return (
                    <input
                        key={idx}
                        type={el.type}
                        placeholder={el.placeholder}
                        required={el.required}
                        onChange={handleChange(idx)}
                    />
                );
            })}
            <button type="submit">Submit</button>
        </form>
    );
};

export default CustomForm;
