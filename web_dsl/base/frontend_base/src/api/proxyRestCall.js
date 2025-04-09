import api from "./index";
import { toast } from "react-toastify";

export const proxyRestCall = async ({
    host,
    port = 443,
    path,
    method = "GET",
    headers = {},
    params = {},
    body = {}
}) => {
    try {
        const restCallPayload = {
            host,
            port,
            path,
            method,
            headers,
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
