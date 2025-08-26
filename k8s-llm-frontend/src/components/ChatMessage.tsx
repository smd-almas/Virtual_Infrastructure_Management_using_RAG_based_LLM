// src/components/ChatMessage.tsx

import { Box, Text, Flex } from '@chakra-ui/react';
import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user';

  return (
    <Flex
      justify={isUser ? 'flex-end' : 'flex-start'}
      my={2}
      px={4}
    >
      <Box
        maxW="75%"
        p={3}
        bg={isUser ? 'blue.500' : 'gray.200'}
        color={isUser ? 'white' : 'black'}
        borderRadius="md"
        textAlign="left"
      >
        {message.content}
      </Box>
    </Flex>
  );
};


export default ChatMessage;
