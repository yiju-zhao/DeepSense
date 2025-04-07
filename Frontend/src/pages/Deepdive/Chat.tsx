import React from 'react';
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Paper,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { HeaderBox, HeaderText } from "../../components/shared/StyledComponents";

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

interface ChatProps {
  selectedPapers: string[];
  papers: Paper[];
  messages: ChatMessage[];
  inputMessage: string;
  onInputChange: (message: string) => void;
  onSendMessage: () => void;
}

export const Chat: React.FC<ChatProps> = ({
  selectedPapers,
  papers,
  messages,
  inputMessage,
  onInputChange,
  onSendMessage,
}) => {
  const chatContainerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (chatContainerRef.current) {
      const scrollContainer = chatContainerRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, [messages]);

  return (
    <>
      <HeaderBox>
        <HeaderText variant='h6'>Chat</HeaderText>
      </HeaderBox>

      <Box display='flex' flexDirection='column' flex={1} position='relative'>
        {selectedPapers.length > 0 ? (
          <>
            {papers
              .filter((paper) => selectedPapers.includes(paper.id))
              .map((paper) => (
                <Box key={paper.id} mb={4}>
                  <Box display='flex' alignItems='center' gap={2} mb={3}>
                    <img
                      src='/assets/img/bulb.svg'
                      alt='bulb'
                      style={{ width: 40, height: 40 }}
                    />
                    <Typography variant='h6' sx={{ fontSize: 24 }}>
                      {paper.title}
                    </Typography>
                  </Box>
                  <Typography variant='body1' color='textSecondary' mb={3}>
                    Overview
                  </Typography>
                  <Typography variant='body1' mb={3}>
                    {paper.abstract}
                  </Typography>
                </Box>
              ))}
          </>
        ) : (
          <>
            <Box display='flex' alignItems='center' gap={2} mb={4}>
              <img
                src='/assets/img/bulb.svg'
                alt='bulb'
                style={{ width: 40, height: 40 }}
              />
              <Typography variant='h6' sx={{ fontSize: 24 }}>
                DeepDive
              </Typography>
            </Box>
            <Typography variant='body1' color='textSecondary'>
              Ask me anything about the selected papers
            </Typography>
          </>
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
            onChange={(e) => onInputChange(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSendMessage();
              }
            }}
          />
          <IconButton
            onClick={onSendMessage}
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
              src='/assets/img/send.svg'
              alt='send'
              style={{ width: 24, height: 24 }}
            />
          </IconButton>
        </ChatInputContainer>
      </Box>
    </>
  );
}; 