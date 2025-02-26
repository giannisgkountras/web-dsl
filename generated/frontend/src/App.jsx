import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";

import MainScreen from "./screens/MainScreen";

import ComplexLayout from "./screens/ComplexLayout";

import Dashboard from "./screens/Dashboard";

const App = () => {
  return (
    <Router>
      <nav>
        <ul>
          <li>
            <Link to="/">Welcome to Our Site</Link>
          </li>

          <li>
            <Link to="/complex">Complex Layout</Link>
          </li>

          <li>
            <Link to="/dashboard">Main Dashboard</Link>
          </li>
        </ul>
      </nav>
      <Routes>
        <Route path="/" element={<MainScreen />} />

        <Route path="/complex" element={<ComplexLayout />} />

        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
};

export default App;
