// src/context/AuthContext.js

import React, { createContext, useState, useEffect, useContext } from "react";
import { userInfo } from "../api/userInfo";
// 1. Create the Context
const AuthContext = createContext();

// 2. Create the AuthProvider Component
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const checkLoggedIn = async () => {
        try {
            // The `withCredentials: true` option is essential.
            // It tells axios to send the HttpOnly cookie with the request.
            const response = await userInfo();
            console.log("User info response:", response);

            // If the request is successful (2xx status), the user is logged in.
            setUser(response);
        } catch (error) {
            // If the request fails (e.g., 401 Unauthorized), the user is not logged in.
            console.log("User is not authenticated.");
            setUser(null);
        } finally {
            // We are done loading, whether we found a user or not.
            setIsLoading(false);
        }
    };

    useEffect(() => {
        checkLoggedIn();
    }, []);

    const value = {
        user,
        isLoading
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 3. Create a custom hook for easy access to the context
export const useAuth = () => {
    return useContext(AuthContext);
};
