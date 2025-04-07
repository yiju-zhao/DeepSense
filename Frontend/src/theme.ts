import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#C00000',
      light: '#E45A5A',
      dark: '#C30F0F',
    },
    secondary: {
      main: '#2E2C2C',
      light: '#736F6F',
      dark: '#181818',
    },
    background: {
      default: '#FFFFFF',
      paper: '#F5F5F5',
    },
    text: {
      primary: '#000000',
      secondary: '#736F6F',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '96px',
      fontWeight: 600,
      lineHeight: '116px',
    },
    h2: {
      fontSize: '48px',
      fontWeight: 600,
      lineHeight: '58px',
    },
    h3: {
      fontSize: '40px',
      fontWeight: 600,
      lineHeight: '48px',
    },
    h4: {
      fontSize: '32px',
      fontWeight: 600,
      lineHeight: '39px',
    },
    body1: {
      fontSize: '15px',
      lineHeight: '30px',
    },
    body2: {
      fontSize: '13px',
      lineHeight: '20px',
    },
    caption: {
      fontSize: '10px',
      lineHeight: '13px',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '40px',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          width: '334px',
          backgroundColor: '#FFFFFF',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#000000',
          boxShadow: 'none',
        },
      },
    },
  },
}); 