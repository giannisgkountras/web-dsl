import React, { createContext, useState, useEffect, useContext, useMemo } from "react";
import { userInfo, websocketAuth } from "../api/userInfo";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [ws_token, setWsToken] = useState("");

    useEffect(() => {
        const initializeAuth = async () => {
            try {
                // Fetch user and ws_token in parallel for efficiency
                const [userResponse, wsTokenResponse] = await Promise.all([userInfo(), websocketAuth()]);

                setUser(userResponse);
                setWsToken(wsTokenResponse?.ws_token || "");
            } catch (error) {
                console.log("User is not authenticated or WebSocket auth failed.", error);
                setUser(null);
                setWsToken("");
            } finally {
                setIsLoading(false);
            }
        };

        initializeAuth();
    }, []);

    // By using useMemo, this 'value' object will only be recreated if
    // user, isLoading, or ws_token actually change.
    const value = useMemo(
        () => ({
            user,
            isLoading,
            ws_token
        }),
        [user, isLoading, ws_token]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    return useContext(AuthContext);
};
