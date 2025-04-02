import api from "./index";
import { toast } from "react-toastify";

export const publish = async (broker, topic, message) => {
    try {
        const response = await api.post("publish", { broker, topic, message });
        if (response?.status === "error") {
            toast.error("Publish request failed:", response.message);
        }
        if (response?.status === "success") {
            toast.success(response.message);
        }
        return response;
    } catch (error) {
        toast.error(error.message);
        return { status: "error", message: error.message };
    }
};
