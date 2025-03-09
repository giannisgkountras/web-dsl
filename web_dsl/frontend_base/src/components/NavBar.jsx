import { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";

const NavBar = ({ screens }) => {
  const [activeUrl, setActiveUrl] = useState("");
  const location = useLocation();

  useEffect(() => {
    // Normalize URLs by removing trailing slashes
    const currentPath = location.pathname.replace(/\/$/, "");
    const matchingScreen = screens.find(
      (screen) => currentPath === screen.url.replace(/\/$/, ""),
    );

    if (matchingScreen) {
      setActiveUrl(matchingScreen.url);
    }
  }, [location.pathname, screens]);

  return (
    <div className="w-full h-14 top-0 flex justify-center">
      <div className="w-1/2 h-full flex items-center justify-evenly px-4 gap-4">
        {screens.map((screen) => {
          const isActive = activeUrl === screen.url;
          return (
            <Link
              key={screen.url} // Use URL as unique key
              to={screen.url}
              className={`text-lg w-full text-center font-bold px-4 py-2 transition-all ${
                isActive
                  ? "border-b-2 border-white text-white"
                  : "text-gray-600 hover:border-b-2 "
              }`}
            >
              {screen.title}
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default NavBar;
