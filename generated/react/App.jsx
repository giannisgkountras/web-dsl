import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";

import MainScreen from "./MainScreen";

import ProfilePage from "./ProfilePage";

import ComplexLayout from "./ComplexLayout";

const App = () => {
  return (
    <Router>
      <div>
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
      </div>
    </Router>
  );
};

export default App;
