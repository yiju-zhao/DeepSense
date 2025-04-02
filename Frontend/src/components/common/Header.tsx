import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { styled } from '@mui/material/styles';

const StyledAppBar = styled(AppBar)({
  backgroundColor: '#FFFFFF',
  color: '#000000',
  boxShadow: 'none',
  borderBottom: '1px solid #E0E0E0',
  height: '200px',
});

const StyledToolbar = styled(Toolbar)({
  height: '100%',
});

const Logo = styled('img')({
  width: '235.48px',
  height: '146px',
  marginLeft: '61px',
  marginTop: '10px',
  marginBottom: '10px',
});

const LanguageSelector = styled(Box)({
  marginLeft: 'auto',
  marginRight: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  alignSelf: 'flex-start',
  marginTop: '24px',
});

const LanguageOption = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '12px 16px',
  cursor: 'pointer',
  borderRadius: '8px',
  '&:hover': {
    backgroundColor: '#F5F5F5',
  },
});

const LanguageText = styled(Typography)({
  fontSize: '16px',
  fontWeight: 500,
});

export const Header: React.FC = () => {
  return (
    <StyledAppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <StyledToolbar>
        <IconButton
          color="inherit"
          edge="start"
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
        <Logo src="/assets/img/cari-digital-logo.svg" alt="CARI Digital Logo" />
        <LanguageSelector>
          <LanguageOption>
            <img src="/assets/img/icons8-美国-48.svg" alt="English" width={32} height={32} />
            <LanguageText>English</LanguageText>
          </LanguageOption>
          <LanguageOption>
            <img src="/assets/img/icons8-中国-48.svg" alt="简体中文" width={32} height={32} />
            <LanguageText>简体中文</LanguageText>
          </LanguageOption>
        </LanguageSelector>
      </StyledToolbar>
    </StyledAppBar>
  );
}; 