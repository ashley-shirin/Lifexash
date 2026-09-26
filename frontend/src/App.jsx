import { Navigate, Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Journal from "./pages/Journal.jsx";
import JournalEditor from "./pages/JournalEditor.jsx";
import Login from "./pages/Login.jsx";
import NoteEditor from "./pages/NoteEditor.jsx";
import Notes from "./pages/Notes.jsx";
import NotFound from "./pages/NotFound.jsx";
import Planner from "./pages/Planner.jsx";
import Profile from "./pages/Profile.jsx";
import Register from "./pages/Register.jsx";

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/planner" element={<Planner />} />
            <Route path="/notes" element={<Notes />} />
            <Route path="/notes/new" element={<NoteEditor />} />
            <Route path="/notes/:noteId" element={<NoteEditor />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/journal/:dateKey" element={<JournalEditor />} />
            <Route path="/profile" element={<Profile />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </>
  );
}
