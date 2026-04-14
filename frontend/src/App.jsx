import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import BookDetailPage from "./pages/BookDetailPage";
import DashboardPage from "./pages/DashboardPage";
import QuestionAnswerPage from "./pages/QuestionAnswerPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/book/:id" element={<BookDetailPage />} />
        <Route path="/qa" element={<QuestionAnswerPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
