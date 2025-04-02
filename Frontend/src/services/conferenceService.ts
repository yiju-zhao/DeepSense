import api, { Conference, ConferenceStats, Paper, Organization } from './api';
import axios, { AxiosError } from 'axios';

const handleApiError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    if (axiosError.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', {
        data: axiosError.response.data,
        status: axiosError.response.status,
        headers: axiosError.response.headers,
      });
      throw new Error(`API Error: ${axiosError.response.status} - ${axiosError.message}`);
    } else if (axiosError.request) {
      // The request was made but no response was received
      console.error('API No Response:', axiosError.request);
      throw new Error('No response received from server');
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Request Setup Error:', axiosError.message);
      throw new Error('Error setting up the request');
    }
  }
  // Not an Axios error
  console.error('Non-Axios Error:', error);
  throw error;
};

export const conferenceService = {
  // Get all conferences
  getAllConferences: async (): Promise<Conference[]> => {
    try {
      const response = await api.get('/conferences');
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error; // TypeScript needs this even though handleApiError always throws
    }
  },

  // Get a specific conference by ID
  getConferenceById: async (id: string): Promise<Conference> => {
    try {
      const response = await api.get(`/conferences/${id}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  // Get conference statistics
  getConferenceStats: async (): Promise<ConferenceStats> => {
    try {
      const response = await api.get('/analytics/conference-stats');
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  // Get papers for a specific conference
  getConferencePapers: async (conferenceId: string): Promise<Paper[]> => {
    try {
      const response = await api.get('/papers', {
        params: { conference: conferenceId }
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  // Get organizations for a specific conference
  getConferenceOrganizations: async (conferenceId: string): Promise<Organization[]> => {
    try {
      const response = await api.get('/organizations', {
        params: { conference: conferenceId }
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }
}; 