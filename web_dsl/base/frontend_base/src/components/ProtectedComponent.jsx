import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedComponent = ({ allowedRoles = [], children }) => {
    const { user } = useAuth();

    if (!user) {
        // No user logged in
        return <LoginPrompt />;
    }

    const isAllowed = allowedRoles.length === 0 || allowedRoles.includes(user?.role);

    if (!isAllowed) {
        // User exists but doesn’t have required role
        return <ForbiddenComponent />;
    }

    // Allowed → show children
    return <>{children}</>;
};

export default ProtectedComponent;

function LoginPrompt() {
    return (
        <div className='flex flex-col items-center justify-center p-6 rounded-2xl bg-[#1A1F29] border border-gray-700 shadow-md text-center max-w-sm mx-auto'>
            <div className='w-12 h-12 flex items-center justify-center rounded-full bg-indigo-600/20 mb-4'>
                <svg
                    xmlns='http://www.w3.org/2000/svg'
                    className='h-6 w-6 text-indigo-400'
                    fill='none'
                    viewBox='0 0 24 24'
                    stroke='currentColor'
                    strokeWidth={2}
                >
                    <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        d='M5.121 17.804A9.969 9.969 0 0112 15c2.21 0 4.236.72 5.879 1.929M15 12a3 3 0 11-6 0 3 3 0 016 0z'
                    />
                </svg>
            </div>

            <h2 className='text-lg font-semibold text-white'>Please Log In</h2>
            <p className='mt-2 text-sm text-gray-400'>You need an account to view this content.</p>

            <Link
                to='/login'
                className='mt-4 px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all duration-300'
            >
                Go to Login
            </Link>
        </div>
    );
}

function ForbiddenComponent() {
    return (
        <div className='flex flex-col items-center justify-center p-6 rounded-2xl bg-[#1A1F29] border border-gray-700 shadow-md text-center max-w-sm mx-auto'>
            <div className='w-12 h-12 flex items-center justify-center rounded-full bg-indigo-600/20 mb-4'>
                <svg
                    xmlns='http://www.w3.org/2000/svg'
                    className='h-6 w-6 text-indigo-400'
                    fill='none'
                    viewBox='0 0 24 24'
                    stroke='currentColor'
                    strokeWidth={2}
                >
                    <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        d='M12 9v2m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4c-.77-1.33-2.7-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z'
                    />
                </svg>
            </div>

            <h2 className='text-lg font-semibold text-white'>Access Restricted</h2>
            <p className='mt-2 text-sm text-gray-400'>You don’t have the required permissions to view this content.</p>
        </div>
    );
}
