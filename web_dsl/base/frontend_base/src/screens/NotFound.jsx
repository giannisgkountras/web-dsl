const NotFound = () => {
    return (
        <div className='w-full min-h-[calc(100vh-66px)] bg-[#0C1017] flex flex-col items-center justify-center text-center'>
            {/* 404 Code */}
            <h1 className='text-8xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-indigo-600 drop-shadow-lg'>
                404
            </h1>

            {/* Title */}
            <p className='mt-4 text-2xl font-semibold text-white'>Page Not Found</p>

            {/* Subtitle */}
            <p className='mt-2 text-gray-400 max-w-md'>
                Sorry, the page you are looking for doesn’t exist or has been moved.
            </p>

            {/* Action button */}
            <a
                href='/'
                className='mt-6 inline-block px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all duration-300 shadow-md'
            >
                Back to Home
            </a>
        </div>
    );
};
export default NotFound;
