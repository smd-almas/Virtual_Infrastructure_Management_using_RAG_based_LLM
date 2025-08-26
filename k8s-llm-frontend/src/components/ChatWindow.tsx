// src/components/ChatWindow.tsx

import { Box } from '@chakra-ui/react';
import ChatMessage from './ChatMessage';
import type { Message } from '../types';

interface ChatWindowProps {
  messages: Message[];
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  isResponding: boolean;
  onStop: () => void;
}

const ChatWindow = ({
  messages,
  input,
  onInputChange,
  onSend,
  isResponding,
  onStop,
}: ChatWindowProps) => {
  return (
    <Box flex={1} px={4} py={2} overflowY="auto" bg="gray.50">
      {messages
        .slice()
        .reverse()
        .map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
    </Box>
  );
};

export default ChatWindow;
