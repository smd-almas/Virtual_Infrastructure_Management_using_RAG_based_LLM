// src/components/LoadingDots.tsx
import React from 'react';
import { HStack, Box} from '@chakra-ui/react';
import { keyframes } from '@chakra-ui/system';

const bounce = keyframes`
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
`;

const LoadingDots: React.FC = () => {
  return (
    <HStack spacing={2} mt={2}>
      {[0, 1, 2].map((i) => (
        <Box
        sx={{
            animation: `${bounce} 1.4s infinite ease-in-out`,
            animationDelay: '0.2s'
          }}
          key={i}
          width="8px"
          height="8px"
          bg="gray.500"
          borderRadius="full"
        />
      ))}
    </HStack>
  );
};

export default LoadingDots;
