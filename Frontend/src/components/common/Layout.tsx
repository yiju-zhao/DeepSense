import React, { useState } from 'react';
import { Box, Container } from '@mui/material';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { styled } from '@mui/material/styles';

interface MainContentProps {
  isSidebarOpen: boolean;
}

const MainContent = styled(Box)<MainContentProps>(({}) => ({
  flexGrow: 1,
  padding: "24px",
  marginLeft: "10px", // isSidebarOpen ?
  transition: "margin-left 0.3s ease",
  backgroundColor: "#FFFFFF",
  minHeight: "100vh",
}));

const ContentContainer = styled(Container)({
  marginTop: '200px',
  paddingTop: '24px',
});

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleSidebarToggle = (isOpen: boolean) => {
    setIsSidebarOpen(isOpen);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <Header />
      <Sidebar onToggle={handleSidebarToggle} />
      <MainContent isSidebarOpen={isSidebarOpen}>
        <ContentContainer maxWidth={false}>
          {children}
        </ContentContainer>
      </MainContent>
    </Box>
  );
}; 