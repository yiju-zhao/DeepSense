import api, { Paper } from './api';

export interface PaperFilters {
  id: string;
  title: string;
  authors: string[];
  conference: string;
  year: number;
  abstract: string;
  keywords: string[];
  citations: number;
  organization: string;
  ai_score?: number;
  reason?: string;
  audience?: string;  
}

export const paperService = {
  // Get all papers with optional filters
  getPapers: async (filters?: PaperFilters): Promise<Paper[]> => {
    const response = await api.get('/papers', { params: filters });
    return response.data;
  },

  // Get a specific paper by ID
  getPaperById: async (id: string): Promise<Paper> => {
    const response = await api.get(`/papers/${id}`);
    return response.data;
  },

  // Search papers by keyword
  searchPapers: async (query: string): Promise<Paper[]> => {
    const response = await api.get('/papers', {
      params: { keyword: query }
    });
    return response.data;
  },

  // Get papers by organization
  getPapersByOrganization: async (organizationId: string): Promise<Paper[]> => {
    const response = await api.get('/papers', {
      params: { organization: organizationId }
    });
    return response.data;
  },

  // Get papers by year
  getPapersByYear: async (year: number): Promise<Paper[]> => {
    const response = await api.get('/papers', {
      params: { year }
    });
    return response.data;
  }
}; 