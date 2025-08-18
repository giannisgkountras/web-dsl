import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // stores decoded user info
    const [token, setToken] = useState(null); // stores access token
    const navigate = useNavigate();

    // Function to login (redirect to OAuth2 provider or handle token exchange)
    const login = async (code) => {
        // Example: Exchange code for token at your backend
        const response = await fetch("/api/auth/callback", {
            method: "POST",
            body: JSON.stringify({ code }),
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        setToken(data.access_token);

        // Decode JWT to extract roles
        const payload = JSON.parse(atob(data.access_token.split(".")[1]));
        setUser(payload);

        navigate("/dashboard");
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        navigate("/login");
    };

    const isAuthorized = (roles = []) => {
        if (!user) return false;
        if (roles.length === 0) return true;
        return roles.some((role) => user.roles?.includes(role));
    };

    return (
        <AuthContext.Provider
            value={{ user, token, login, logout, isAuthorized }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export function useAuth() {
    return useContext(AuthContext);
}
