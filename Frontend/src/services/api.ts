import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Conference {
  id: string;
  name: string;
  logo: string;
  description: string;
  totalPapers: number;
  averageCitation: number;
  yearRange: string;
  rank: number;
  impactScore: number;
  acceptanceRate: string;
  submissionDeadline: string;
  notificationDate: string;
  conferenceDate: string;
}

export interface Organization {
  id: string;
  name: string;
  description: string;
  total_papers: number;
  conferences: string[];
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  conference: string;
  year: number;
  abstract: string;
  keywords: string[];
  citations: number;
  organization: string;
}

export interface ConferenceStats {
  total_conferences: number;
  total_papers: number;
  total_organizations: number;
  conferences_by_year: Record<string, number>;
}

export interface OrganizationStats {
  total_organizations: number;
  total_papers: number;
  organizations_by_conference: Record<string, number>;
}

export default api; 