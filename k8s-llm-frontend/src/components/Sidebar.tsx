// src/components/Sidebar.tsx
import React from 'react';
import { Box, VStack, Text, Button } from '@chakra-ui/react';

interface SidebarProps {
  history: string[];
  onSelect: (index: number) => void;
}

// Utility to extract up to 5, fallback to 4 or 3 words
const getPreview = (text: string): string => {
  const words = text.trim().split(/\s+/);
  if (words.length >= 5) return words.slice(0, 5).join(" ");
  if (words.length >= 4) return words.slice(0, 4).join(" ");
  return words.slice(0, 3).join(" ");
};

const Sidebar: React.FC<SidebarProps> = ({ history, onSelect }) => {
  return (
    <Box
      w="250px"
      h="100vh"
      bg="gray.800"
      color="white"
      p={4}
      overflowY="auto"
    >
      <Text fontSize="xl" fontWeight="bold" mb={4}>
        🔧 Chat History
      </Text>
      <VStack align="start" spacing={2}>
        {history.map((item, idx) => (
          <Button
            key={idx}
            variant="ghost"
            colorScheme="whiteAlpha"
            onClick={() => onSelect(idx)}
            w="100%"
            justifyContent="start"
            whiteSpace="nowrap"
            overflow="hidden"
            textOverflow="ellipsis"
            fontWeight="normal"
          >
            {getPreview(item)}
          </Button>
        ))}
      </VStack>
    </Box>
  );
};

export default Sidebar;
