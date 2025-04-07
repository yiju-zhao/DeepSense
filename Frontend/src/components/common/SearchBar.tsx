import React, { useState } from 'react';
import { 
  TextField, 
  InputAdornment, 
  IconButton,
  Box,
  Typography
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  label?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = 'Search papers...',
  label = 'Search'
}) => {
  const [query, setQuery] = useState('');

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setQuery(value);
    onSearch(value);
  };

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', my: 2 }}>
      <TextField
        fullWidth
        variant="outlined"
        label={label}
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: query && (
            <InputAdornment position="end">
              <IconButton size="small" onClick={handleClear}>
                <ClearIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      {query && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
          Showing results for "{query}"
        </Typography>
      )}
    </Box>
  );
}; 