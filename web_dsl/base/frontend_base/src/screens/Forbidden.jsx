import { Link } from "react-router-dom";

export default function Forbidden() {
    return (
        <div className='flex flex-col items-center justify-center min-h-[calc(100vh-66px)] text-center bg-[#0C1017] px-4'>
            {/* Icon / Symbol */}
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
                        d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L4.34 16c-.77 1.333.192 3 1.732 3z'
                    />
                </svg>
            </div>

            {/* Title */}
            <h1 className='text-3xl font-semibold text-white'>Access Restricted</h1>

            {/* Subtitle */}
            <p className='mt-3 text-gray-400 max-w-md'>
                Sorry, you don’t have permission to view this page. If you think this is a mistake, please contact
                support.
            </p>

            {/* Action */}
            <Link
                to='/'
                className='mt-6 px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all duration-300 shadow-md'
            >
                Back to Home
            </Link>
        </div>
    );
}
