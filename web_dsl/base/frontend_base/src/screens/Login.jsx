import { useState, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const Login = () => {
    const appTitle = window.document.title;
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const usernameRef = useRef(null);
    const passwordRef = useRef(null);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleLogin = (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        const username = usernameRef.current.value;
        const password = passwordRef.current.value;

        // simple mock example (replace with real API later)
        if (username === "admin" && password === "1234") {
            login(username, "admin"); // role = admin
        } else if (username === "user" && password === "1234") {
            login(username, "user"); // role = user
        } else {
            setError("Invalid credentials.");
        }
        navigate("/");
        setLoading(false);
    };
    return (
        <div className='w-screen h-screen flex items-center justify-center bg-[#080b0f]'>
            <div className='flex bg-[#0c1116] w-1/4 h-1/2 flex-col items-center justify-center rounded-xl shadow-lg border-1 border-[#26272b] relative'>
                <h1 className='text-2xl mb-4 font-semibold'>Sign in to {appTitle}</h1>
                <form
                    className='no-style mt-4 w-2/3 h-1/2 flex justify-evenly items-center flex-col'
                    onSubmit={handleLogin}
                >
                    <label className='block mb-2 text-gray-300 w-full text-start'>Username</label>
                    <input
                        className='w-full'
                        placeholder='Enter your username'
                        type='text'
                        ref={usernameRef}
                        autoFocus
                    ></input>
                    <label className='block mb-2 text-gray-300 w-full text-start mt-4'>Password</label>
                    <input
                        className='w-full'
                        placeholder='Enter your password'
                        type='password'
                        ref={passwordRef}
                    ></input>
                    <button
                        type='submit'
                        className='mt-5 bg-blue-500 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-600 w-full disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-500'
                        disabled={loading}
                    >
                        {loading ? <span className='animate-pulse'>Loading...</span> : "Login"}
                    </button>
                </form>
                {error && <p className='text-red-500 text-sm mt-2 absolute bottom-3'>{error}</p>}
            </div>
        </div>
    );
};

export default Login;
