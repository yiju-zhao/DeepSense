import React, { useRef, useEffect, useState } from 'react';
import { Typography, Box, Grid, Tabs, Tab, CircularProgress, Alert } from '@mui/material';
import { styled } from '@mui/material/styles';
import type { Conference, ConferenceStats, Paper } from '../services/api';
import { conferenceService } from '../services/conferenceService';
import { paperService } from '../services/paperService';

const TabsContainer = styled(Box)({
  borderBottom: '1px solid #E0E0E0',
  marginBottom: '48px',
  position: 'sticky',
  top: '200px',
  backgroundColor: '#FFFFFF',
  zIndex: 1,
});

const StyledTabs = styled(Tabs)({
  '& .MuiTabs-indicator': {
    backgroundColor: '#C00000',
  },
});

const StyledTab = styled(Tab)({
  fontSize: '16px',
  fontWeight: 500,
  color: '#000000',
  '&.Mui-selected': {
    color: '#C00000',
  },
});

const Section = styled(Box)({
  scrollMarginTop: '280px', // Account for header height + tabs height
});

const Title = styled(Typography)({
  marginBottom: '48px',
});

const SubTitle = styled(Typography)({
  marginBottom: '32px',
});

const ConferenceGrid = styled(Grid)({
  marginBottom: '48px',
});

const ConferenceCard = styled(Box)({
  background: '#FFFFFF',
  borderRadius: '23px',
  padding: '24px',
  boxShadow: '0px 4px 4px rgba(0, 0, 0, 0.25)',
  marginBottom: '32px',
});

const ConferenceLogo = styled('img')({
  width: '197px',
  height: '169px',
  borderRadius: '23px',
  marginBottom: '16px',
});

const ConferenceName = styled(Typography)({
  fontSize: '36px',
  fontWeight: 700,
  lineHeight: '44px',
  marginBottom: '16px',
});

const ConferenceDescription = styled(Typography)({
  fontSize: '13px',
  lineHeight: '20px',
  color: '#736F6F',
  marginBottom: '16px',
});

const ConferenceStats = styled(Typography)({
  fontSize: '15px',
  fontWeight: 600,
  lineHeight: '21px',
  color: '#736F6F',
});

const LoadingContainer = styled(Box)({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '200px',
});

const OverviewGrid = styled(Grid)({
  marginBottom: '48px',
});

const StatCard = styled(Box)({
  textAlign: 'center',
  padding: '24px',
});

const StatValue = styled(Typography)({
  fontSize: '48px',
  fontWeight: 700,
  lineHeight: '56px',
  color: '#000000',
  marginBottom: '16px',
});

const StatLabel = styled(Typography)({
  fontSize: '24px',
  fontWeight: 500,
  lineHeight: '32px',
  color: '#736F6F',
});

const PaperGrid = styled(Grid)({
  marginBottom: '48px',
});

const PaperCard = styled(Box)({
  background: '#FFFFFF',
  borderRadius: '12px',
  overflow: 'hidden',
  boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
});

const PaperImage = styled('img')({
  width: '100%',
  height: '200px',
  objectFit: 'cover',
});

const PaperContent = styled(Box)({
  padding: '20px',
  flexGrow: 1,
  display: 'flex',
  flexDirection: 'column',
});

const PaperTitle = styled(Typography)({
  fontSize: '20px',
  fontWeight: 600,
  marginBottom: '12px',
  color: '#000000',
});

const PaperDescription = styled(Typography)({
  fontSize: '14px',
  color: '#666666',
  marginBottom: '16px',
  flexGrow: 1,
});

const PaperFooter = styled(Box)({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '12px 20px',
  borderTop: '1px solid #E0E0E0',
});

const PaperType = styled(Box)({
  padding: '4px 12px',
  borderRadius: '16px',
  fontSize: '12px',
  fontWeight: 500,
  backgroundColor: '#F5F5F5',
});

const PaperDate = styled(Typography)({
  fontSize: '12px',
  color: '#666666',
});

export const DeepSight: React.FC = () => {
  const [selectedTab, setSelectedTab] = React.useState(0);
  const [conferences, setConferences] = useState<Conference[]>([]);
  const [conferenceStats, setConferenceStats] = useState<ConferenceStats | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const topReportRef = useRef<HTMLDivElement>(null);
  const conferenceRef = useRef<HTMLDivElement>(null);
  const organizationRef = useRef<HTMLDivElement>(null);
  const keywordRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [conferencesData, statsData, papersData] = await Promise.all([
          conferenceService.getAllConferences(),
          conferenceService.getConferenceStats(),
          paperService.getPapers()
        ]);
        setConferences(conferencesData);
        setConferenceStats(statsData);
        setPapers(papersData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data. Please try again later.';
        setError(errorMessage);
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    const refs = [topReportRef, conferenceRef, organizationRef, keywordRef];
    refs[newValue]?.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const renderOverview = () => {
    if (loading) {
      return (
        <LoadingContainer>
          <CircularProgress sx={{ color: '#C00000' }} />
        </LoadingContainer>
      );
    }

    if (error || !conferenceStats) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Failed to load conference statistics'}
        </Alert>
      );
    }

    const stats = [
      { label: 'Total Conference', value: conferenceStats.total_conferences },
      { label: 'Total Papers', value: conferenceStats.total_papers.toLocaleString() },
      { label: 'Years Covered', value: '10' },
      { label: 'Avg Papers/Year', value: '4,500' }
    ];

    return (
      <OverviewGrid container spacing={3}>
        {stats.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.label}>
            <StatCard>
              <StatValue variant="h3">
                {stat.value}
              </StatValue>
              <StatLabel variant="h6">
                {stat.label}
              </StatLabel>
            </StatCard>
          </Grid>
        ))}
      </OverviewGrid>
    );
  };

  const renderPaper = () => {
    if (loading) {
      return (
        <LoadingContainer>
          <CircularProgress sx={{ color: '#C00000' }} />
        </LoadingContainer>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      );
    }

    return (
      <PaperGrid container spacing={3}>
        {papers.map((paper) => (
          <Grid item xs={12} sm={6} md={4} key={paper.id}>
            <PaperCard>
              <PaperImage src={`/assets/img/paper/paper${parseInt(paper.id) % 3}.svg`} alt={paper.title} />
              <PaperContent>
                <PaperTitle>{paper.title}</PaperTitle>
                <PaperDescription>{paper.abstract}</PaperDescription>
              </PaperContent>
              <PaperFooter>
                <PaperType>{paper.conference}</PaperType>
                <PaperDate>{new Date(paper.year, 0).getFullYear()}</PaperDate>
              </PaperFooter>
            </PaperCard>
          </Grid>
        ))}
      </PaperGrid>
    );
  };

  const renderConferenceContent = () => {
    if (loading) {
      return (
        <LoadingContainer>
          <CircularProgress sx={{ color: '#C00000' }} />
        </LoadingContainer>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      );
    }

    return (
      <ConferenceGrid container spacing={3}>
        {conferences.map((conference) => (
          <Grid item xs={12} md={6} lg={4} key={conference.id}>
            <ConferenceCard>
              <ConferenceLogo src={conference.logo} alt={`${conference.name} logo`} />
              <ConferenceName>{conference.name}</ConferenceName>
              <ConferenceDescription>{conference.description}</ConferenceDescription>
              <ConferenceStats>
                Total Papers: {conference.totalPapers.toLocaleString()}<br />
                Average Citation: {conference.averageCitation}<br />
                Impact Score: {conference.impactScore}<br />
                Acceptance Rate: {conference.acceptanceRate}<br />
                Next Deadline: {new Date(conference.submissionDeadline).toLocaleDateString()}
              </ConferenceStats>
            </ConferenceCard>
          </Grid>
        ))}
      </ConferenceGrid>
    );
  };

  return (
    <Box>
      <TabsContainer>
        <StyledTabs value={selectedTab} onChange={handleTabChange}>
          <StyledTab label="Top Report" />
          <StyledTab label="Conference" />
          <StyledTab label="Organization" />
          <StyledTab label="Keyword" />
        </StyledTabs>
      </TabsContainer>

      <Section ref={topReportRef}>
        <Title variant="h2">Research Report</Title>
        {renderPaper()}
      </Section>

      <Section ref={conferenceRef}>
        <Title variant="h2">Conference</Title>
        <SubTitle variant="h3" align="center">Overview</SubTitle>
        {renderOverview()}
        <SubTitle variant="h3" align="center">Top Conferences</SubTitle>
        {renderConferenceContent()}
      </Section>

      <Section ref={organizationRef}>
        <Title variant="h2">Organization</Title>
        {/* Organization content will go here */}
      </Section>

      <Section ref={keywordRef}>
        <Title variant="h2">Keyword</Title>
        {/* Keyword content will go here */}
      </Section>
    </Box>
  );
}; 