import { Link } from "react-router-dom";

export default function Forbidden() {
    return (
        <div className='flex flex-col items-center justify-center h-screen text-center'>
            <h1 className='text-4xl font-bold text-red-600'>Forbidden</h1>
            <p className='mt-4 text-lg text-gray-700'>You don’t have permission to access this page.</p>
            <Link to='/' className='mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'>
                Go Back Home
            </Link>
        </div>
    );
}
