import api from "./index";
import { toast } from "react-toastify";

export const proxyRestCall = async ({
    name,
    path,
    method = "GET",
    params = {},
    body = {}
}) => {
    try {
        const restCallPayload = {
            name,
            path,
            method,
            params,
            body
        };

        const response = await api.post("restcall", restCallPayload);

        if (!response) {
            toast.error("No response from proxy.");
            return { status: "error", message: "No response from proxy" };
        }
        return response;
    } catch (error) {
        toast.error("Proxy REST call failed: " + error.message);
        return { status: "error", message: error.message };
    }
};
