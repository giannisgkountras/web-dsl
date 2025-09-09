import { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NavBar = ({ screens, includeLogin = false }) => {
    const [activeUrl, setActiveUrl] = useState("");
    const location = useLocation();
    const appTitle = window.document.title;
    const backendBaseURL = import.meta.env.VITE_API_BASE_URL;
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
        <div className='w-full h-[56px] bg-[#0C1017] flex items-center justify-between px-6 relative shadow-md border-b border-[#26272b]'>
            {/* Left - Logo */}
            <div className='w-1/3 text-white font-bold text-lg'>{appTitle}</div>

            {/* Center - Navigation (absolute centered, independent of right side) */}
            <div className='flex w-1/3 items-center justify-center gap-8'>
                {screens.map((screen) => {
                    const isActive = activeUrl === screen.url;
                    return (
                        <Link
                            key={screen.url}
                            to={screen.url}
                            className={`relative text-xl font-medium transition-colors duration-300 ${
                                isActive
                                    ? "text-white after:content-[''] after:absolute after:left-0 after:-bottom-1 after:h-[2px] after:w-full after:bg-indigo-500"
                                    : "text-gray-400 hover:text-white"
                            }`}
                        >
                            {screen.title}
                        </Link>
                    );
                })}
            </div>

            {/* Right - User / Auth */}
            <div className='w-1/3 flex items-center justify-end gap-4'>
                {!isLoading && user ? (
                    <>
                        {/* Avatar */}
                        <div className='w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-xs'>
                            {user.email.charAt(0).toUpperCase()}
                        </div>
                        <span className='hidden sm:block text-gray-300 truncate max-w-[140px]' title={user.email}>
                            {user.email}
                        </span>
                        <a
                            href={`${backendBaseURL}/auth/logout`}
                            className='px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-all duration-300 shadow-md'
                        >
                            Logout
                        </a>
                    </>
                ) : (
                    !isLoading && (
                        <a
                            href={`${backendBaseURL}/auth/login`}
                            className='px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-all duration-300 shadow-md'
                        >
                            Login
                        </a>
                    )
                )}
            </div>
        </div>
    );
};

export default NavBar;
