import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { paperService, PaperFilters } from '../services/paperService';
// import { Paper } from '../services/api';

export const useSearch = () => {
  const [filters, setFilters] = useState<PaperFilters>({});
  const [searchQuery, setSearchQuery] = useState('');

  const { data: papers, isLoading, error } = useQuery({
    queryKey: ['papers', filters, searchQuery],
    queryFn: () => {
      if (searchQuery) {
        return paperService.searchPapers(searchQuery);
      }
      return paperService.getPapers(filters);
    },
  });

  const updateFilters = useCallback((newFilters: Partial<PaperFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  const search = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  return {
    papers: papers || [],
    isLoading,
    error,
    filters,
    searchQuery,
    updateFilters,
    clearFilters,
    search,
  };
}; 