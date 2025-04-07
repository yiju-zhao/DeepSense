import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Card,
  Chip,
  IconButton,
  Button,
  Pagination,
  Tooltip,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { paperService } from "../services/paperService";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import DatePicker from "@mui/lab/DatePicker";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";

const ITEMS_PER_PAGE = 5;

// Predefined colors for categories - softer pastel colors
const CATEGORY_COLORS = [
  "rgba(244, 199, 199, 0.8)", // Soft Red
  "rgba(187, 222, 251, 0.8)", // Soft Blue
  "rgba(200, 230, 201, 0.8)", // Soft Green
  "rgba(255, 224, 178, 0.8)", // Soft Orange
  "rgba(225, 190, 231, 0.8)", // Soft Purple
  "rgba(178, 223, 219, 0.8)", // Soft Teal
  "rgba(248, 187, 208, 0.8)", // Soft Pink
  "rgba(255, 236, 179, 0.8)", // Soft Amber
  "rgba(197, 202, 233, 0.8)", // Soft Indigo
  "rgba(215, 204, 200, 0.8)", // Soft Brown
  "rgba(255, 255, 255, 0.8)", // Soft White
];

const CategoryCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: "12px",
}));

const TopPaperCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: "12px",
}));

const CollectCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: "12px",
}));

const PaperCard = styled(Card)<{ index: number }>(({ theme, index }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: "12px",
  backgroundColor: index % 2 === 0 ? "#fff" : "#f5f5f5",
  position: "relative",
  "&:hover .hover-buttons": {
    display: "flex",
  },
}));

const HoverButtons = styled(Box)({
  display: "none",
  position: "absolute",
  top: "8px",
  right: "8px",
  gap: "8px",
});

const CategoryChip = styled(Chip)<{ categoryColor?: string }>(
  ({ categoryColor }) => ({
    margin: "0 4px 4px 0",
    backgroundColor: categoryColor || CATEGORY_COLORS[0],
    color: "#666666", // Darker gray text for better contrast with pastel backgrounds
    fontWeight: 500,
    "&:hover": {
      backgroundColor: categoryColor || CATEGORY_COLORS[0],
      opacity: 0.85,
    },
  })
);

const MetricsBox = styled(Box)({
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginTop: "8px",
});

const StyledTypography = styled(Typography)<{ maxWidth?: string | number }>(
  ({ maxWidth = "400px" }) => ({
    // TODO: maxWidth should be calculated from parent element instead of hardcoded 400px
    display: "inline-block",
    maxWidth,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    verticalAlign: "middle",
  })
);

const AuthorStyledTypography = styled(StyledTypography)({
  color: "gray",
  fontSize: "14px",
  marginBottom: "8px",
});

export const Dataset: React.FC = () => {
  const [papers, setPapers] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [categoryColorMap, setCategoryColorMap] = useState<
    Record<string, string>
  >({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [topPapersCount, setTopPapersCount] = useState(5);
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const allPapers = await paperService.getPapers();
        setPapers(allPapers);
        setTotalPages(Math.ceil(allPapers.length / ITEMS_PER_PAGE));

        // Extract unique categories
        const uniqueCategories = new Set<string>();
        allPapers.forEach((paper) => {
          if (paper.keywords) {
            paper.keywords.forEach((keyword: string) =>
              uniqueCategories.add(keyword)
            );
          }
        });
        const categoriesArray = Array.from(uniqueCategories);
        setCategories(categoriesArray);

        // Create color mapping for categories
        const colorMap: Record<string, string> = {};
        categoriesArray.forEach((category, index) => {
          colorMap[category] = CATEGORY_COLORS[index % CATEGORY_COLORS.length];
        });
        setCategoryColorMap(colorMap);
      } catch (error) {
        console.error("Error fetching papers:", error);
      }
    };

    fetchPapers();
  }, []);

  const getCurrentPagePapers = () => {
    const startIndex = (page - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    return papers.slice(startIndex, endIndex);
  };

  const handlePageChange = (
    _event: React.ChangeEvent<unknown>,
    value: number
  ) => {
    setPage(value);
  };

  const handleDateChange = (date: Date | null) => {
    setSelectedDate(date);
    setOpen(false);
  };

  return (
    <>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, position: 'relative' }}>
        <IconButton onClick={() => setOpen(true)}>
          <CalendarTodayIcon />
        </IconButton>
        <Typography variant="h2">
          {selectedDate?.toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
        </Typography>
        {open && (
          <Box sx={{ position: 'absolute', top: '100%', left: 0, zIndex: 1300 }}>
            <DatePicker
              open={open}
              onClose={() => setOpen(false)}
              value={selectedDate}
              onChange={handleDateChange}
              PopperProps={{
                placement: 'bottom-start',
                sx: {
                  zIndex: 1300
                }
              }}
              renderInput={(params: any) => (
                <TextField
                  {...params}
                  sx={{ display: 'none' }}
                />
              )}
            />
          </Box>
        )}
      </Box>
      <Box sx={{ display: "flex", gap: 3, p: 3 }}>
        {/* Left Column */}
        <Box sx={{ width: "30%" }}>
          <CategoryCard>
            <Typography variant='h6' gutterBottom>
              Categories
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
              {categories.map((category) => (
                <CategoryChip
                  key={category}
                  label={category}
                  categoryColor={categoryColorMap[category]}
                />
              ))}
            </Box>
          </CategoryCard>

          <TopPaperCard>
            <Typography variant='h6' gutterBottom>
              Top Papers
            </Typography>

            {papers.slice(0, topPapersCount).map((paper) => (
              <Box key={paper.id} sx={{ mb: 2 }}>
                <Tooltip title={paper.title} arrow>
                  <StyledTypography variant='subtitle1' maxWidth='400px'>
                    {/* TODO: need to calculate maxWidth from parent element instead of hardcoded 300px */}
                    {paper.title}
                  </StyledTypography>
                </Tooltip>

                <Tooltip title={paper.authors?.join(", ")} arrow>
                  <AuthorStyledTypography variant='subtitle1' maxWidth='400px'>
                    {paper.authors?.join(", ")}
                  </AuthorStyledTypography>
                </Tooltip>
              </Box>
            ))}
            {papers.length > topPapersCount && (
              <Button
                variant='text'
                fullWidth
                onClick={() => setTopPapersCount((prev) => prev + 5)}
                sx={{ mt: 1 }}
              >
                Load More
              </Button>
            )}
          </TopPaperCard>

          <CollectCard>
            <Typography variant='h6' gutterBottom>
              Collect
            </Typography>
            {/* Collect content will be implemented later */}
          </CollectCard>
        </Box>

        {/* Right Column - Papers */}
        <Box sx={{ width: "70%" }}>
          {getCurrentPagePapers().map((paper, index) => (
            <PaperCard key={paper.id} index={index}>
              <HoverButtons className='hover-buttons'>
                <Button variant='contained' color='primary' size='small'>
                  AI Insight
                </Button>
                <Button variant='contained' color='secondary' size='small'>
                  Deepdive
                </Button>
              </HoverButtons>

              <Typography variant='h6' sx={{ mb: 1, fontWeight: "bold" }}>
                {paper.title}
              </Typography>
              <AuthorStyledTypography maxWidth='600px'>
                {paper.authors?.join(", ")}
              </AuthorStyledTypography>

              <Box sx={{ mb: 2 }}>
                {paper.keywords?.map((keyword: string) => (
                  <CategoryChip
                    key={keyword}
                    label={keyword}
                    size='small'
                    categoryColor={categoryColorMap[keyword]}
                  />
                ))}
              </Box>

              <Tooltip title={`Abstract: ${paper.abstract}`} arrow>
                <StyledTypography variant='body2' maxWidth='600px'>
                  <Typography component='span' sx={{ mr: 2 }}>
                    <b>Abstract:</b>
                  </Typography>
                  {paper.abstract}
                </StyledTypography>
              </Tooltip>

              <MetricsBox>
                <Box sx={{ display: "flex", alignItems: "center" }}>
                  <Typography component='span' sx={{ mr: 2 }}>
                    <b>AI Score:</b> {paper.ai_score || "N/A"}
                  </Typography>
                  <Tooltip title={`Reason: ${paper.reason || "N/A"}`} arrow>
                    <StyledTypography maxWidth='400px'>
                      <b>Reason:</b> {paper.reason || "N/A"}
                    </StyledTypography>
                  </Tooltip>
                  <Typography component='span'>
                    <b>Audience:</b> {paper.audience || "N/A"}
                  </Typography>
                </Box>
                <Box>
                  <IconButton size='small'>
                    <ThumbUpIcon />
                  </IconButton>
                  <IconButton size='small'>
                    <ThumbDownIcon />
                  </IconButton>
                </Box>
              </MetricsBox>
            </PaperCard>
          ))}

          <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color='primary'
            />
          </Box>
        </Box>
      </Box>
    </>
  );
};

export default Dataset;
