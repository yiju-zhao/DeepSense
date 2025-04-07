import React from 'react';
import {
  Box,
  Typography,
  IconButton,
  Checkbox,
  Button,
  Tooltip,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { HeaderBox, HeaderText } from "../../components/shared/StyledComponents";

const PaperTitle = styled(Typography)({
  fontWeight: 700,
  fontSize: "18px",
  lineHeight: "1.4",
  marginBottom: "4px",
});

const PaperInfo = styled(Typography)({
  color: "#666666",
  fontSize: "14px",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  display: "block"
});

const IconContainer = styled(Box)<{ isCollapsed: boolean }>(
  ({ isCollapsed }) => ({
    display: "flex",
    flexDirection: isCollapsed ? "column" : "row",
    gap: isCollapsed ? "16px" : "8px",
    alignItems: "center",
  })
);

interface Paper {
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

interface SourcesProps {
  papers: Paper[];
  selectedPapers: string[];
  isSourcesCollapsed: boolean;
  onSourcesCollapse: () => void;
  onPaperSelect: (paperId: string) => void;
  onSelectAll: () => void;
  onDeleteSelected: () => void;
}

const truncateText = (text: string, limit: number) => {
  if (text.length <= limit) return text;
  return text.slice(0, limit) + "...";
};

export const Sources: React.FC<SourcesProps> = ({
  papers,
  selectedPapers,
  isSourcesCollapsed,
  onSourcesCollapse,
  onPaperSelect,
  onSelectAll,
  onDeleteSelected,
}) => {
  const formatPaperInfo = (paper: Paper) => {
    const fullText = `${paper.conference} | ${paper.authors.join(", ")} | ${paper.organization}`;
    return truncateText(fullText, 50);
  };

  return (
    <>
      <HeaderBox>
        {!isSourcesCollapsed && <HeaderText>Sources</HeaderText>}
        <IconContainer isCollapsed={isSourcesCollapsed}>
          <IconButton onClick={onSourcesCollapse}>
            <img
              src='/assets/img/fold-box.svg'
              alt='collapse'
              style={{
                transform: isSourcesCollapsed ? "rotate(180deg)" : "none",
                width: isSourcesCollapsed ? "70%" : "20px",
                height: isSourcesCollapsed ? "70%" : "20px",
                maxWidth: "30px",
                maxHeight: "30px",
                minWidth: "16px",
                minHeight: "16px",
              }}
            />
          </IconButton>
          <IconButton onClick={onDeleteSelected}>
            <img
              src='/assets/img/delete-icon.svg'
              alt='delete'
              style={{
                width: "20px",
                height: "20px",
              }}
            />
          </IconButton>
        </IconContainer>
      </HeaderBox>

      {!isSourcesCollapsed && (
        <>
          <Box
            display='flex'
            alignItems='center'
            mb={3}
            justifyContent='space-between'
          >
            <Typography variant='h6' sx={{ fontSize: "18px" }}>
              Select All
            </Typography>
            <Checkbox
              checked={selectedPapers.length === papers.length}
              onChange={onSelectAll}
            />
          </Box>

          {papers.map((paper) => (
            <Box key={paper.id} mb={3}>
              <Box
                display='flex'
                alignItems='flex-start'
                justifyContent='space-between'
              >
                <Box flex={1} pr={2} maxWidth="calc(100% - 40px)">
                  <PaperTitle>{paper.title}</PaperTitle>
                  <Tooltip title={`${paper.conference} | ${paper.authors.join(", ")} | ${paper.organization}`}>
                    <PaperInfo>
                      {formatPaperInfo(paper)}
                    </PaperInfo>
                  </Tooltip>
                </Box>
                <Box>
                  <Checkbox
                    checked={selectedPapers.includes(paper.id)}
                    onChange={() => onPaperSelect(paper.id)}
                  />
                </Box>
              </Box>
            </Box>
          ))}

          <Box sx={{ mt: 2 }}>
            <Typography variant='body2' color='text.secondary' mb={2}>
              {selectedPapers.length} source
              {selectedPapers.length !== 1 ? "s" : ""} selected
            </Typography>
            <Button
              variant='outlined'
              fullWidth
              sx={{
                borderRadius: "24px",
                color: "#C00000",
                borderColor: "#C00000",
                "&:hover": {
                  borderColor: "#900000",
                  backgroundColor: "rgba(192, 0, 0, 0.04)",
                },
              }}
              startIcon={<Typography>+</Typography>}
            >
              Add More Source
            </Button>
          </Box>
        </>
      )}
    </>
  );
}; 