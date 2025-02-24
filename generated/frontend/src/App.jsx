import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";

import MainScreen from "./screens/MainScreen";

import ProfilePage from "./screens/ProfilePage";

import ComplexLayout from "./screens/ComplexLayout";

const App = () => {
    return (
        <Router>
            <nav>
                <ul>
                    <li>
                        <Link to="/home">Welcome to Our Site</Link>
                    </li>

                    <li>
                        <Link to="/profile">Your profile</Link>
                    </li>

                    <li>
                        <Link to="/complex">Complex Layout</Link>
                    </li>
                </ul>
            </nav>
            <Routes>
                <Route path="/home" element={<MainScreen />} />

                <Route path="/profile" element={<ProfilePage />} />

                <Route path="/complex" element={<ComplexLayout />} />
            </Routes>
        </Router>
    );
};

export default App;
