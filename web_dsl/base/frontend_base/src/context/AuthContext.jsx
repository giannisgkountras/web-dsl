import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // Example state (in real app, fetch from API or localStorage)
    const [user, setUser] = useState(null);
    // user = { username: "john", role: "admin" } or null if not signed in

    const login = (username, role) => setUser({ username, role });
    const logout = () => setUser(null);

    return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
