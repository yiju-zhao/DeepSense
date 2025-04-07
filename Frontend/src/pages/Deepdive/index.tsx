import React, { useState, useEffect, useRef } from "react";
import { Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import { Sources } from "./Sources";
import { Chat } from "./Chat";
import { Studio } from "./Studio";

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

export const DeepDive: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
  const [isSourcesCollapsed, setIsSourcesCollapsed] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(613); // 10:13 in seconds
  const [showOptions, setShowOptions] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [showCustomizeModal, setShowCustomizeModal] = useState(false);
  const [showAudioPlayer, setShowAudioPlayer] = useState(false);
  
  const progressRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    // Fetch papers on component mount
    fetch("http://localhost:8000/api/v1/papers")
      .then((res) => res.json())
      .then((data) => setPapers(data))
      .catch((error) => console.error("Error fetching papers:", error));
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

  const handleDeleteSelected = () => {
    if (selectedPapers.length === 0) return;
    
    setPapers((prevPapers) =>
      prevPapers.filter((paper) => !selectedPapers.includes(paper.id))
    );
    setSelectedPapers([]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      message: inputMessage,
      response: "",
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

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
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? { message: inputMessage, response: data.response }
            : msg
        )
      );
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
    }
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

  const handleCustomize = () => {
    setShowCustomizeModal(true);
    setShowAudioPlayer(false);
  };

  const handleCloseModal = () => {
    setShowCustomizeModal(false);
    setShowAudioPlayer(true);
  };

  const handleGenerate = () => {
    setShowAudioPlayer(true);
  };

  return (
    <Box display='flex' height='100vh' bgcolor='white' gap={1}>
      {/* Sources Column */}
      <Box
        flex={isSourcesCollapsed ? "0 0 8%" : "0 0 27%"}
        sx={{ transition: "flex 0.3s ease" }}
      >
        <ColumnContainer>
          <Sources
            papers={papers}
            selectedPapers={selectedPapers}
            isSourcesCollapsed={isSourcesCollapsed}
            onSourcesCollapse={() => setIsSourcesCollapsed(!isSourcesCollapsed)}
            onPaperSelect={handlePaperSelect}
            onSelectAll={handleSelectAll}
            onDeleteSelected={handleDeleteSelected}
          />
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
            <Chat
              selectedPapers={selectedPapers}
              papers={papers}
              messages={messages}
              inputMessage={inputMessage}
              onInputChange={setInputMessage}
              onSendMessage={handleSendMessage}
            />
          </ColumnContainer>
        </Box>

        {/* Studio Column */}
        <Box
          flex={isSourcesCollapsed ? "0 0 45%" : "0 0 38%"}
          sx={{ transition: "flex 0.3s ease" }}
        >
          <ColumnContainer>
            <Studio
              showAudioPlayer={showAudioPlayer}
              showCustomizeModal={showCustomizeModal}
              currentTime={currentTime}
              duration={duration}
              isPlaying={isPlaying}
              showOptions={showOptions}
              onPlayPause={handlePlayPause}
              onProgressClick={handleProgressClick}
              onDragStart={handleDragStart}
              onCloseModal={handleCloseModal}
              onCustomize={handleCustomize}
              onGenerate={handleGenerate}
              onToggleOptions={() => setShowOptions(!showOptions)}
            />
          </ColumnContainer>
        </Box>
      </Box>

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
    </Box>
  );
};