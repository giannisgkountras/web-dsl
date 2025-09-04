import api from "./index";
import { toast } from "react-toastify";

export const userInfo = async () => {
    try {
        const response = await api.get("me");
        return response;
    } catch (error) {
        toast.error(error.message);
        return { status: "error", message: error.message };
    }
};
