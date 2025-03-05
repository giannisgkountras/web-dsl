import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";

import MainScreen from "./screens/MainScreen";

import ComplexLayout from "./screens/ComplexLayout";

import Dashboard from "./screens/Dashboard";

import Games from "./screens/Games";

import NavBar from "./components/NavBar";

const App = () => {
  return (
    <div className="screen-container">
      <Router>
        <NavBar
          screens={[
            { url: "/", title: "Welcome to Our Site" },

            { url: "/complex", title: "Complex Layout" },

            { url: "/dashboard", title: "Main Dashboard" },

            { url: "/games", title: "Games" },
          ]}
        />

        <Routes>
          <Route path="/" element={<MainScreen />} />

          <Route path="/complex" element={<ComplexLayout />} />

          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/games" element={<Games />} />
        </Routes>
      </Router>
    </div>
  );
};

export default App;
