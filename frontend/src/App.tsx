import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import ToastContainer from './components/Toast';
import LandingPage from './pages/LandingPage';
import Workbench from './pages/Workbench';
import HistoryPage from './pages/HistoryPage';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <ToastContainer />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/app" element={<Workbench />} />
            <Route path="/app/history" element={<HistoryPage />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
