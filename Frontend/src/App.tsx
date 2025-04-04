import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from './theme';
import { Layout } from './components/common/Layout';
import { DeepSight } from './pages/DeepSight';
import { DailyPaper } from './pages/DailyPaper';
import { DailyNews } from './pages/DailyNews';
import { DeepDive } from './pages/DeepDive';
import { Dashboard } from './pages/Dashboard';
import { Dataset } from './pages/Dataset';

const queryClient = new QueryClient();

function App() {
  return (
      <QueryClientProvider client={queryClient}>
          <ThemeProvider theme={theme}>
              <CssBaseline />
              <BrowserRouter>
                  <Layout>
                      <Routes>
                          <Route path="/" element={<DeepSight />} />
                          <Route path="/deepsight" element={<DeepSight />} />
                          <Route path="/dailypaper" element={<DailyPaper />} />
                          <Route path="/dailynews" element={<DailyNews />} />
                          <Route path="/dailynews/dashboard" element={<Dashboard />} />
                          <Route path="/dailynews/dataset" element={<Dataset />} />
                          <Route path="/dailynews/deepdive" element={<DeepDive />} />
                      </Routes>
                  </Layout>
              </BrowserRouter>
          </ThemeProvider>
      </QueryClientProvider>
  );
}

export default App; 