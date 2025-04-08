import api from "./index";
import { toast } from "react-toastify";

export const proxyRestCall = async ({
    baseUrl,
    path,
    method = "GET",
    headers = {},
    params = {},
    body = {},
    port = 443
}) => {
    try {
        const restCallPayload = {
            host: new URL(baseUrl).hostname,
            port,
            path,
            base_url: baseUrl,
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
