// src/components/ResourceModal.tsx

import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  Box,
  Code,
} from '@chakra-ui/react';
import type { FC } from 'react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  resource: string;
  data: any[];
}

const ResourceModal: FC<Props> = ({ isOpen, onClose, resource, data }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{resource} Resources</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Box maxH="70vh" overflowY="auto" whiteSpace="pre-wrap">
            <Code p={4} width="100%" whiteSpace="pre" fontSize="sm">
              {JSON.stringify(data, null, 2)}
            </Code>
          </Box>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default ResourceModal;
