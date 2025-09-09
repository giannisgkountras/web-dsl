const Login = () => {
    const backendBaseURL = import.meta.env.VITE_API_BASE_URL;
    return (
        <div className='flex flex-col items-center justify-center min-h-[calc(100vh-66px)] bg-[#0C1017] text-center px-4'>
            {/* Icon */}
            <div className='w-16 h-16 flex items-center justify-center rounded-full bg-indigo-600/20 mb-6'>
                <svg
                    xmlns='http://www.w3.org/2000/svg'
                    className='h-8 w-8 text-indigo-400'
                    fill='none'
                    viewBox='0 0 24 24'
                    stroke='currentColor'
                    strokeWidth={2}
                >
                    <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        d='M12 11c0-.414.336-.75.75-.75h.5a.75.75 0 010 1.5h-.5a.75.75 0 01-.75-.75zM12 15h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
                    />
                </svg>
            </div>

            {/* Title */}
            <h1 className='text-3xl font-semibold text-white'>Login Required</h1>

            {/* Subtitle */}
            <p className='mt-3 text-gray-400 max-w-md'>
                You need to be logged in to access this page. Please sign in to continue.
            </p>

            {/* Login Button */}
            <a
                href={`${backendBaseURL}/auth/login`}
                className='mt-6 px-8 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all duration-300 shadow-md'
            >
                Log In
            </a>
        </div>
    );
};

export default Login;
