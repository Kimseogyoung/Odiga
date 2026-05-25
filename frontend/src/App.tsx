import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import PlannerPage from './pages/PlannerPage';
import CoursePage from './pages/CoursePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/planner/:sessionId" element={<PlannerPage />} />
        <Route path="/course/:shareToken" element={<CoursePage />} />
      </Routes>
    </BrowserRouter>
  );
}
