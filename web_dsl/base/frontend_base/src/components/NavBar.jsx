import { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NavBar = ({ screens }) => {
    const [activeUrl, setActiveUrl] = useState("");
    const location = useLocation();
    const { user, isLoading } = useAuth();

    useEffect(() => {
        // Normalize URLs by removing trailing slashes
        const currentPath = location.pathname.replace(/\/$/, "");
        const matchingScreen = screens.find((screen) => currentPath === screen.url.replace(/\/$/, ""));

        if (matchingScreen) {
            setActiveUrl(matchingScreen.url);
        }
    }, [location.pathname, screens]);

    return (
        <div className='w-full h-[56px] top-0 flex justify-center'>
            <div className='w-1/2 h-full flex items-center justify-evenly px-4 gap-4'>
                {screens.map((screen) => {
                    const isActive = activeUrl === screen.url;
                    return (
                        <Link
                            key={screen.url} // Use URL as unique key
                            to={screen.url}
                            className={`text-lg w-full text-center font-bold px-4 py-2 transition-all ${
                                isActive ? "border-b-2 border-white text-white" : "text-gray-600 hover:border-b-2 "
                            }`}
                        >
                            {screen.title}
                        </Link>
                    );
                })}
                {!isLoading && user && (
                    <div>
                        <span>Welcome, {user.email}!</span>
                        {/* The logout link simply points to your backend's logout endpoint */}
                        <a href='http://localhost:8321/auth/logout' style={{ marginLeft: "1rem" }}>
                            Logout
                        </a>
                    </div>
                )}

                {/* State 3: Finished loading, and no user is logged in */}
                {!isLoading && !user && <a href='http://localhost:8321/auth/login'>Login</a>}
            </div>
        </div>
    );
};

export default NavBar;
