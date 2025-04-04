import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  Box,
  IconButton,
} from '@mui/material';
import { styled } from '@mui/material/styles';

const drawerWidth = 300; // width of the sidebar

const StyledDrawer = styled(Drawer)<{ open: boolean }>(({ open }) => ({
  width: open ? drawerWidth : "60px", // 60 px is the shrinked width of the sidebar
  flexShrink: 0, // Ensures the drawer maintains its width even when the window is resized

  transition: "width 0.3s ease",
  "& .MuiDrawer-paper": {
    width: open ? drawerWidth : "60px",
    boxSizing: "border-box",
    borderRight: "1px solid #E0E0E0",
    backgroundColor: "#FFFFFF",
    transition: "width 0.3s ease",
    overflowX: "hidden",
  },
}));

const DrawerContent = styled(Box)({
  marginTop: '200px',
  padding: '24px 0',
  position: 'relative',
});

const ToggleButton = styled(IconButton)<{ open: boolean }>(({ open }) => ({
  position: 'absolute',
  top: '10px',
  left: open ? '24px' : '8px',
  transition: 'left 0.3s ease',
}));

const MenuItem = styled(ListItemButton)({
  margin: '16px 5px',
  padding: '0 24px',
  '&.Mui-selected': {
    backgroundColor: '#F5F5F5',
    borderRadius: '17px',
    '& .MuiListItemText-primary': {
      color: '#C00000',
    },
  },
  '&:hover': {
    backgroundColor: '#F5F5F5',
    borderRadius: '17px',
  },
});

const MenuText = styled(Typography)({
  fontSize: '32px',
  fontWeight: 600,
  lineHeight: '40px',
});

const BackButton = styled(ListItemButton)({
  margin: '16px 5px',
  padding: '0 24px',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
});

const HomeText = styled(Typography)({
  fontSize: "24px",
  fontWeight: 600,
  lineHeight: "32px",
  color: "#929292",
});

interface SidebarProps {
  onToggle: (isOpen: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(true);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    onToggle(!isOpen);
  };

  const isDailynewsRoute = location.pathname.startsWith('/dailynews');

  const mainMenuItems = [
    { text: 'Homepage', path: '/' },
    { text: 'Dailysight', path: '/dailysight' },
    { text: 'Dailypaper', path: '/dailypaper' },
    { text: 'Dailynews', path: '/dailynews', hasSubMenu: true },
  ];

  const dailynewsSubMenuItems = [
    { text: 'Dashboard', path: '/dailynews/dashboard' },
    { text: 'Dataset', path: '/dailynews/dataset' },
    { text: 'Deepdive', path: '/dailynews/deepdive' },
  ];

  const handleMenuClick = (item: { text: string; path: string; hasSubMenu?: boolean }) => {
    if (item.hasSubMenu) {
      navigate(item.path);
    } else {
      navigate(item.path);
    }
  };

  return (
    <StyledDrawer variant='permanent' open={isOpen}>
      <DrawerContent>
        <ToggleButton open={isOpen} onClick={handleToggle}>
          <img
            src='/assets/img/fold-sidebar.svg'
            alt='toggle sidebar'
            style={{
              transform: isOpen ? "none" : "rotate(180deg)",
              transition: "transform 0.3s ease",
              width: "24px",
              height: "24px",
            }}
          />
        </ToggleButton>
        <Box sx={{ height: "24px" }} />

        {isDailynewsRoute && isOpen ? (
          <>
            <BackButton onClick={() => navigate("/")}>
              <img
                src='/assets/img/arrow-left.svg'
                alt='back'
                style={{ width: "24px", height: "24px" }}
              />
              <HomeText>Home</HomeText>
            </BackButton>
            <List>
              {dailynewsSubMenuItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <MenuItem
                    selected={location.pathname === item.path}
                    onClick={() => navigate(item.path)}
                  >
                    <ListItemText
                      primary={<MenuText>{item.text}</MenuText>}
                      sx={{ textAlign: "left" }}
                    />
                  </MenuItem>
                </ListItem>
              ))}
            </List>
          </>
        ) : (
          <List>
            {mainMenuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <MenuItem
                  selected={location.pathname === item.path}
                  onClick={() => handleMenuClick(item)}
                  sx={{
                    opacity: isOpen ? 1 : 0,
                    transition: "opacity 0.2s ease",
                  }}
                >
                  <ListItemText
                    primary={<MenuText>{item.text}</MenuText>}
                    sx={{ textAlign: "left" }}
                  />
                </MenuItem>
              </ListItem>
            ))}
          </List>
        )}
      </DrawerContent>
    </StyledDrawer>
  );
}; 