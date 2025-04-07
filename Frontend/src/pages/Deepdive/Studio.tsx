import React from 'react';
import {
  Box,
  Typography,
  IconButton,
  Button,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { HeaderBox, HeaderText } from "../../components/shared/StyledComponents";

const AudioPlayerContainer = styled(Box)({
  padding: '24px',
  backgroundColor: '#FFFFFF',
  borderRadius: '12px',
  boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)',
  marginTop: '24px',
  display: 'flex',
  width: '100%',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '24px'
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
  width: "100%",
  padding: "0 0px"
});

const TimeDisplay = styled(Typography)({
  color: "#484848",
  fontSize: "14px",
});

const OptionsMenu = styled(Box)({
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

const GenerateAudioBox = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '24px',
  textAlign: 'center',
});

const ButtonContainer = styled(Box)({
  display: 'flex',
  width: '100%',
  '& > button': {
    flex: 1,
    '&:not(:last-child)': {
      marginRight: '16px' // add margin right to all buttons except the last one
    }
  }
});

const CustomButton = styled(Button)({
  flex: 1,
  borderRadius: '8px',
  padding: '12px 24px',
  textTransform: 'none',
  fontSize: '16px',
});

const UploadModal = styled(Box)({
  position: 'fixed',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  backgroundColor: 'white',
  borderRadius: '16px',
  padding: '32px',
  width: '600px',
  maxWidth: '90vw',
  boxShadow: '0px 4px 24px rgba(0, 0, 0, 0.1)',
  zIndex: 1000,
});

const ModalOverlay = styled(Box)({
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  zIndex: 999,
});

const UploadArea = styled(Box)({
  border: '2px dashed #E0E0E0',
  borderRadius: '8px',
  padding: '48px',
  marginTop: '24px',
  marginBottom: '24px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '16px',
});

const FileTypesText = styled(Typography)({
  '& .highlight': {
    color: '#C00000',
    fontWeight: 600,
  },
});

interface StudioProps {
  showAudioPlayer: boolean;
  showCustomizeModal: boolean;
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  showOptions: boolean;
  onPlayPause: () => void;
  onProgressClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  onDragStart: () => void;
  onCloseModal: () => void;
  onCustomize: () => void;
  onGenerate: () => void;
  onToggleOptions: () => void;
}

export const Studio: React.FC<StudioProps> = ({
  showAudioPlayer,
  showCustomizeModal,
  currentTime,
  duration,
  isPlaying,
  showOptions,
  onPlayPause,
  onProgressClick,
  onDragStart,
  onCloseModal,
  onCustomize,
  onGenerate,
  onToggleOptions,
}) => {
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  };

  return (
    <>
      <HeaderBox>
        <HeaderText>Studio</HeaderText>
      </HeaderBox>

      <Typography variant='h6'>Panel Audio</Typography>

      {showAudioPlayer ? (
        <AudioPlayerContainer>
          <AudioTitle>
            Large Language Models in Scientific Discovery
          </AudioTitle>

          <ProgressBarContainer
            onClick={onProgressClick}
            onMouseDown={onDragStart}
          >
            <img
              src='/assets/img/progress-bar.svg'
              alt='progress'
              style={{ width: "100%", height: "4px" }}
            />
            <ProgressDot
              style={{
                left: `${(currentTime / duration) * 100}%`,
              }}
            >
              <img
                src='/assets/img/progress-dot.svg'
                alt='progress dot'
                style={{ width: "16px", height: "16px" }}
              />
            </ProgressDot>
          </ProgressBarContainer>

          <AudioControls>
            <Box display='flex' alignItems='center'>
              <IconButton 
                onClick={onPlayPause}
                sx={{ padding: "3px" }}
              >
                <img
                  src='/assets/img/play.svg'
                  alt={isPlaying ? "pause" : "play"}
                  style={{
                    width: "46px",
                    height: "46px",
                  }}
                />
              </IconButton>
              <TimeDisplay sx={{ marginLeft: "20px" }}>
                {formatTime(currentTime)}/{formatTime(duration)}
              </TimeDisplay>
            </Box>

            <Box position='relative'>
              <IconButton 
                onClick={onToggleOptions}
                sx={{ padding: "12px" }}
              >
                <img
                  src='/assets/img/three-dot-option.svg'
                  alt='options'
                  style={{ width: "24px", height: "24px" }}
                />
              </IconButton>
              {showOptions && (
                <OptionsMenu>
                  <OptionItem>
                    <img
                      src='/assets/img/playspeed.svg'
                      alt='playspeed'
                      style={{ width: "20px", height: "20px" }}
                    />
                    <Typography>Playspeed</Typography>
                  </OptionItem>
                  <OptionItem>
                    <img
                      src='/assets/img/download.svg'
                      alt='download'
                      style={{ width: "20px", height: "20px" }}
                    />
                    <Typography>Download</Typography>
                  </OptionItem>
                  <OptionItem>
                    <img
                      src='/assets/img/delete-icon.svg'
                      alt='delete'
                      style={{ width: "20px", height: "20px" }}
                    />
                    <Typography>Delete</Typography>
                  </OptionItem>
                </OptionsMenu>
              )}
            </Box>
          </AudioControls>
        </AudioPlayerContainer>
      ) : (
        <AudioPlayerContainer>
          <GenerateAudioBox>
            <img
              src='/assets/img/generate-audio.svg'
              alt='generate audio'
              style={{ width: '35px', height: '35px' }}
            />
            <Typography>Click to generate Audio.</Typography>
            <ButtonContainer>
              <CustomButton
                variant="outlined"
                onClick={onCustomize}
              >
                Customize
              </CustomButton>
              <CustomButton
                variant="contained"
                onClick={onGenerate}
              >
                Generate
              </CustomButton>
            </ButtonContainer>
          </GenerateAudioBox>
        </AudioPlayerContainer>
      )}

      {showCustomizeModal && (
        <>
          <ModalOverlay onClick={onCloseModal} />
          <UploadModal>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h4">Deepdive</Typography>
              <IconButton onClick={onCloseModal}>
                <img src="/assets/img/close.svg" alt="close" />
              </IconButton>
            </Box>
            
            <Typography variant="body1" mb={4}>
              After adding Source, Deepdive can based on this generate important information for you.
            </Typography>

            <UploadArea>
              <img
                src='/assets/img/upload-source.svg'
                alt='upload'
                style={{ width: '70px', height: '69px' }}
              />
              <Typography>Upload Source</Typography>
              <Typography color="textSecondary">
                Drag and drop or select a file to upload.
              </Typography>
            </UploadArea>

            <FileTypesText>
              <span className="highlight">Supported file types:</span> PDF, .txt, Markdown, audio (e.g., mp3)
            </FileTypesText>

            <Box display="flex" alignItems="center" justifyContent="space-between" mt={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <img src="/assets/img/source-restrictions.svg" alt="restrictions" />
                <Typography>Source restrictions</Typography>
              </Box>
              <Typography>1/50</Typography>
            </Box>
          </UploadModal>
        </>
      )}
    </>
  );
}; 