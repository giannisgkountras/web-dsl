import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = ({ allowedRoles }) => {
    const { user } = useAuth();

    if (!user) {
        // not logged in → go to login
        return <Navigate to='/login' replace />;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
        // logged in but wrong role go to forbidden page
        return <Navigate to='/forbidden' replace />;
    }

    return <Outlet />; // render child routes
};

export default ProtectedRoute;
