import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Paper,
  Checkbox,
  Button,
} from "@mui/material";
import { styled } from "@mui/material/styles";

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

interface ChatMessage {
  message: string;
  response: string;
}

const ColumnContainer = styled(Box)({
  height: "calc(100vh - 300px)",
  display: "flex",
  flexDirection: "column",
  border: "1px solid #e0e0e0",
  borderRadius: "12px",
  padding: "20px",
  overflow: "auto",
  margin: "20px",
  backgroundColor: "white",
  boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
});

// Chat
const ChatContainer = styled(Box)({
  flex: 1,
  display: "flex",
  flexDirection: "column",
  gap: "16px",
  overflowY: "auto",
  padding: "16px",
  marginBottom: "16px",
  "&::-webkit-scrollbar": {
    width: "8px",
  },
  "&::-webkit-scrollbar-track": {
    background: "#f1f1f1",
    borderRadius: "4px",
  },
  "&::-webkit-scrollbar-thumb": {
    background: "#888",
    borderRadius: "4px",
  },
});

const ChatInputContainer = styled(Box)({
  display: "flex",
  alignItems: "center",
  gap: "12px",
  padding: "16px",
  backgroundColor: "white",
  borderTop: "1px solid #E0E0E0",
  position: "sticky",
  bottom: 0,
});

const ChatInput = styled(TextField)({
  flex: 1,
  "& .MuiOutlinedInput-root": {
    borderRadius: "20px",
    backgroundColor: "#F5F5F5",
  },
});

const MessageBubble = styled(Paper)<{ isUser: boolean }>(({ isUser }) => ({
  padding: "12px 16px",
  maxWidth: "70%",
  alignSelf: isUser ? "flex-end" : "flex-start",
  backgroundColor: isUser ? "#C00000" : "#F5F5F5",
  color: isUser ? "white" : "inherit",
  borderRadius: "16px",
  marginBottom: "8px",
}));

const HeaderBox = styled(Box)({
  borderBottom: "1px solid #E0E0E0",
  marginBottom: "20px",
  paddingBottom: "12px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
});

const HeaderText = styled(Typography)({
  color: "#C00000",
  fontWeight: 600,
  fontSize: "24px",
});

const PaperTitle = styled(Typography)({
  fontWeight: 700,
  fontSize: "18px",
  lineHeight: "1.4",
  marginBottom: "4px",
});

const PaperInfo = styled(Typography)({
  color: "#666666",
  fontSize: "14px",
});

const IconContainer = styled(Box)<{ isCollapsed: boolean }>(
  ({ isCollapsed }) => ({
    display: "flex",
    flexDirection: isCollapsed ? "column" : "row",
    gap: isCollapsed ? "16px" : "8px",
    alignItems: "center",
  })
);

// Audio Player
const AudioPlayerContainer = styled(Box)({
  padding: "12px",
  backgroundColor: "#FFFFFF",
  borderRadius: "12px",
  boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
  marginTop: "24px",
});

const AudioTitle = styled(Typography)({
  fontSize: "18px",
  fontWeight: 600,
  marginBottom: "24px",
});

const ProgressBarContainer = styled(Box)({
  position: "relative",
  width: "100%",
  height: "24px",
  display: "flex",
  alignItems: "center",
  cursor: "pointer",
});

const ProgressDot = styled(Box)({
  position: "absolute",
  cursor: "grab",
  width: "16px",
  height: "14px",
  // transform: "translateX(-30%)",
  transform: "translateY(-50%)",
  "&:active": {
    cursor: "grabbing",
  },
});

const AudioControls = styled(Box)({
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginTop: "16px",
});

const TimeDisplay = styled(Typography)({
  color: "#484848",
  fontSize: "14px",
});

const OptionsMenu = styled(Paper)({
  position: "absolute",
  right: 0,
  top: "100%",
  marginTop: "8px",
  padding: "8px 0",
  backgroundColor: "white",
  boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
  borderRadius: "8px",
  zIndex: 1000,
});

const OptionItem = styled(Box)({
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "8px 16px",
  cursor: "pointer",
  "&:hover": {
    backgroundColor: "#F5F5F5",
  },
});

export const DeepDive: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
  const [isSourcesCollapsed, setIsSourcesCollapsed] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const chatContainerRef = React.useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(613); // 10:13 in seconds
  const [showOptions, setShowOptions] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const progressRef = React.useRef<HTMLDivElement>(null);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  useEffect(() => {
    // Fetch papers on component mount
    fetch("http://localhost:8000/api/v1/papers")
      .then((res) => res.json())
      .then((data) => setPapers(data))
      .catch((error) => console.error("Error fetching papers:", error));
  }, []);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      const scrollContainer = chatContainerRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
      // TODO: this doesn't work
      requestAnimationFrame(() => {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      });
    }
  };

  // Scroll when messages change
  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Clear chat when selected papers change
  React.useEffect(() => {
    setMessages([]);
  }, [selectedPapers]);

  // Also scroll when component mounts
  React.useEffect(() => {
    scrollToBottom();
  }, []);

  const handleSelectAll = () => {
    if (selectedPapers.length === papers.length) {
      setSelectedPapers([]);
    } else {
      setSelectedPapers(papers.map((paper) => paper.id));
    }
  };

  const handlePaperSelect = (paperId: string) => {
    setSelectedPapers((prev) =>
      prev.includes(paperId)
        ? prev.filter((id) => id !== paperId)
        : [...prev, paperId]
    );
  };

  const handleDeselectAll = () => {
    setSelectedPapers([]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    // Add user message immediately
    const userMessage = {
      message: inputMessage,
      response: "",
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    // Scroll after adding user message
    setTimeout(scrollToBottom, 100);

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: inputMessage,
          response: "",
        }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();

      // Update the messages array with the response
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? { message: inputMessage, response: data.response }
            : msg
        )
      );

      // Scroll after receiving response
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? {
                message: inputMessage,
                response: "Sorry, there was an error processing your message.",
              }
            : msg
        )
      );

      // Scroll after error message
      setTimeout(scrollToBottom, 100);
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  };

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (progressRef.current && !isDragging) {
      const rect = progressRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = x / rect.width;
      const newTime = percentage * duration;
      setCurrentTime(newTime);
      if (audioRef.current) {
        audioRef.current.currentTime = newTime;
      }
    }
  };

  const handleDragStart = () => {
    setIsDragging(true);
  };

  const handleDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging && progressRef.current) {
      const rect = progressRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const percentage = x / rect.width;
      const newTime = percentage * duration;
      setCurrentTime(newTime);
    }
  };

  const handleDragEnd = () => {
    if (isDragging && audioRef.current) {
      const percentage = currentTime / duration;
      audioRef.current.currentTime = percentage * duration;
      setIsDragging(false);
    }
  };

  useEffect(() => {
    const handleMouseUp = () => {
      if (isDragging) {
        handleDragEnd();
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        handleDrag(e as unknown as React.MouseEvent<HTMLDivElement>);
      }
    };

    document.addEventListener("mouseup", handleMouseUp);
    document.addEventListener("mousemove", handleMouseMove);

    return () => {
      document.removeEventListener("mouseup", handleMouseUp);
      document.removeEventListener("mousemove", handleMouseMove);
    };
  }, [isDragging]);

  return (
    <Box display='flex' height='100vh' bgcolor='white' gap={1}>
      {/* Sources Column */}
      <Box
        flex={isSourcesCollapsed ? "0 0 8%" : "0 0 27%"}
        sx={{ transition: "flex 0.3s ease" }}
      >
        <ColumnContainer>
          <HeaderBox>
            {!isSourcesCollapsed && <HeaderText>Sources</HeaderText>}
            <IconContainer isCollapsed={isSourcesCollapsed}>
              <IconButton
                onClick={() => setIsSourcesCollapsed(!isSourcesCollapsed)}
              >
                <img
                  src="/assets/img/fold-box.svg"
                  alt="collapse"
                  style={{
                    transform: isSourcesCollapsed ? "rotate(180deg)" : "none",
                    width: "20px",
                    height: "20px",
                  }}
                />
              </IconButton>
              <IconButton onClick={handleDeselectAll}>
                <img
                  src="/assets/img/delete-icon.svg"
                  alt="delete"
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
                  onChange={handleSelectAll}
                />
              </Box>

              {papers.map((paper) => (
                <Box key={paper.id} mb={3}>
                  <Box
                    display='flex'
                    alignItems='flex-start'
                    justifyContent='space-between'
                  >
                    <Box flex={1} pr={2}>
                      <PaperTitle>{paper.title}</PaperTitle>
                      <PaperInfo>
                        {paper.conference} | {paper.authors.join(", ")} |{" "}
                        {paper.organization}
                      </PaperInfo>
                    </Box>
                    <Checkbox
                      checked={selectedPapers.includes(paper.id)}
                      onChange={() => handlePaperSelect(paper.id)}
                    />
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
        </ColumnContainer>
      </Box>

      {/* Container for Chat and Studio to share Sources' space */}
      <Box flex='1' display='flex' gap={1}>
        {/* Chat Column */}
        <Box
          flex={isSourcesCollapsed ? "0 0 55%" : "0 0 62%"}
          sx={{ transition: "flex 0.3s ease" }}
        >
          <ColumnContainer>
            <HeaderBox>
              <HeaderText variant='h6'>Chat</HeaderText>
            </HeaderBox>

            <Box
              display='flex'
              flexDirection='column'
              flex={1}
              position='relative'
            >
              {selectedPapers.length > 0 ? (
                <>
                  {papers
                    .filter((paper) => selectedPapers.includes(paper.id))
                    .map((paper) => (
                      <Box key={paper.id} mb={4}>
                        <Box display='flex' alignItems='center' gap={2} mb={3}>
                          <img
                            src="/assets/img/bulb.svg"
                            alt="bulb"
                            style={{ width: 24, height: 24 }}
                          />
                          <Typography variant='h6'>{paper.title}</Typography>
                        </Box>
                        <Typography
                          variant='body1'
                          color='textSecondary'
                          mb={3}
                        >
                          Overview
                        </Typography>
                        <Typography variant='body1' mb={3}>
                          {paper.abstract}
                        </Typography>
                      </Box>
                    ))}
                </>
              ) : (
                <Typography variant='h6' mb={3}>
                  Select a paper to start chatting
                </Typography>
              )}

              <ChatContainer ref={chatContainerRef}>
                {messages.map((msg, index) => (
                  <React.Fragment key={index}>
                    <MessageBubble isUser={true}>
                      <Typography>{msg.message}</Typography>
                    </MessageBubble>
                    {msg.response && (
                      <MessageBubble isUser={false}>
                        <Typography>{msg.response}</Typography>
                      </MessageBubble>
                    )}
                  </React.Fragment>
                ))}
              </ChatContainer>

              <ChatInputContainer>
                <ChatInput
                  fullWidth
                  placeholder='Type your message...'
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
                <IconButton
                  onClick={handleSendMessage}
                  sx={{
                    width: 40,
                    height: 40,
                    backgroundColor: "#F5F5F5",
                    "&:hover": {
                      backgroundColor: "#E0E0E0",
                    },
                  }}
                >
                  <img
                    src="/assets/img/send.svg"
                    alt="send"
                    style={{ width: 24, height: 24 }}
                  />
                </IconButton>
              </ChatInputContainer>
            </Box>
          </ColumnContainer>
        </Box>

        {/* Studio Column */}
        <Box
          flex={isSourcesCollapsed ? "0 0 45%" : "0 0 38%"}
          sx={{ transition: "flex 0.3s ease" }}
        >
          <ColumnContainer>
            <HeaderBox>
              <HeaderText>Studio</HeaderText>
            </HeaderBox>

            <Typography variant='h6'>Panel Audio</Typography>

            <AudioPlayerContainer>
              <AudioTitle>
                Large Language Models in Scientific Discovery
              </AudioTitle>

              <ProgressBarContainer
                ref={progressRef}
                onClick={handleProgressClick}
                onMouseDown={handleDragStart}
              >
                <img
                  src="/assets/img/progress-bar.svg"
                  alt="progress"
                  style={{ width: "100%", height: "4px" }}
                />
                <ProgressDot
                  style={{
                    left: `${(currentTime / duration) * 100}%`,
                  }}
                >
                  <img
                    src="/assets/img/progress-dot.svg"
                    alt="progress dot"
                    style={{ width: "16px", height: "16px" }}
                  />
                </ProgressDot>
              </ProgressBarContainer>

              <AudioControls>
                <Box display='flex' alignItems='center' gap={2}>
                  <IconButton onClick={handlePlayPause}>
                    <img
                      src="/assets/img/play.svg"
                      alt={isPlaying ? "pause" : "play"}
                      style={{
                        width: "46px",
                        height: "41px",
                      }}
                    />
                  </IconButton>
                  <TimeDisplay>
                    {formatTime(currentTime)}/{formatTime(duration)}
                  </TimeDisplay>
                </Box>

                <Box position='relative'>
                  <IconButton onClick={() => setShowOptions(!showOptions)}>
                    <img
                      src="/assets/img/three-dot-option.svg"
                      alt="options"
                      style={{ width: "24px", height: "24px" }}
                    />
                  </IconButton>

                  {showOptions && (
                    <OptionsMenu>
                      <OptionItem>
                        <img
                          src="/assets/img/playspeed.svg"
                          alt="playspeed"
                          style={{ width: "20px", height: "20px" }}
                        />
                        <Typography>Playspeed</Typography>
                      </OptionItem>
                      <OptionItem>
                        <img
                          src="/assets/img/download.svg"
                          alt="download"
                          style={{ width: "20px", height: "20px" }}
                        />
                        <Typography>Download</Typography>
                      </OptionItem>
                      <OptionItem>
                        <img
                          src="/assets/img/delete-icon.svg"
                          alt="delete"
                          style={{ width: "20px", height: "20px" }}
                        />
                        <Typography>Delete</Typography>
                      </OptionItem>
                    </OptionsMenu>
                  )}
                </Box>
              </AudioControls>

              <audio
                ref={audioRef}
                src='http://localhost:8000/api/v1/audio'
                onTimeUpdate={() => {
                  if (audioRef.current && !isDragging) {
                    setCurrentTime(audioRef.current.currentTime);
                  }
                }}
                onLoadedMetadata={() => {
                  if (audioRef.current) {
                    setDuration(audioRef.current.duration);
                  }
                }}
              />
            </AudioPlayerContainer>
          </ColumnContainer>
        </Box>
      </Box>
    </Box>
  );
};

export default DeepDive;
