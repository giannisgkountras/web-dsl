import ky from "ky";
import { toast } from "react-toastify";

const apiUrl = import.meta.env.VITE_API_BASE_URL;
const apiKey = import.meta.env.VITE_API_KEY;

const rootApi = ky.extend({
    timeout: false,
    prefixUrl: `${apiUrl}`,
    headers: {
        "X-API-Key": apiKey
    },
    credentials: "include"
});
const api = {
    post: async (path, json) => {
        try {
            return await rootApi.post(path, { json }).json();
        } catch (error) {
            toast.error(error.message);
        }
    },
    get: async (path) => {
        try {
            return await rootApi.get(path).json();
        } catch (error) {
            toast.error(error.message);
        }
    }
};

export default api;
