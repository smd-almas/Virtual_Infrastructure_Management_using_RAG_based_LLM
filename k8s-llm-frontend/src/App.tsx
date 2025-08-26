import { useState } from 'react';
import {
  Box,
  Button,
  Container,
  Flex,
  Input,
  useToast,
  useDisclosure,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiSend, FiSquare } from 'react-icons/fi';
import ChatWindow from './components/ChatWindow';
import Sidebar from './components/Sidebar';
import MetricsPanel from './components/MetricsPanel';
import ResourceDropdown from './components/ResourceDropdown';
import ResourceModal from './components/ResourceModal';
import LoadingDots from './components/LoadingDots';
import type { Message } from './types';
import client from './api/client';
import { getPreview } from './utils/formatters';

import {
  getPods,
  getDeployments,
  getServices,
  getConfigMaps,
  getNamespaces,
  getNodes,
} from './api/resources';

const App = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! How can I help you with Kubernetes today?' },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [resourceData, setResourceData] = useState<any[]>([]);
  const [resourceType, setResourceType] = useState('');
  const toast = useToast();
  const modal = useDisclosure();

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages: Message[] = [
      { role: 'user', content: input },
      ...messages,
    ];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const res = await client.post('/ask', { query: input });
      const { type, result } = res.data;
      setMessages([{ role: 'assistant', content: result }, ...newMessages]);

    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send message.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistory = (index: number) => {
    const selected = messages[index];
    if (selected) setMessages([selected]);
  };

  const apiMap: Record<string, () => Promise<any>> = {
    Pods: getPods,
    Deployments: getDeployments,
    Services: getServices,
    ConfigMaps: getConfigMaps,
    Namespaces: getNamespaces,
    Nodes: getNodes,
  };

  const handleResourceSelect = async (resource: string) => {
    setResourceType(resource);
    try {
      const fetchFunc = apiMap[resource];
      if (!fetchFunc) throw new Error(`Unknown resource: ${resource}`);

      const res = await fetchFunc();
      setResourceData(res.data);
      modal.onOpen();
    } catch (error) {
      toast({
        title: 'Error fetching resource',
        description: 'Check backend or network connection.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    }
  };

  return (
    <Flex height="100vh">
      <Sidebar
        history={messages.map((msg) => getPreview(msg.content))}
        onSelect={handleSelectHistory}
      />

      <Flex flexDirection="column" flex={1}>
        <Flex justify="space-between" align="center" p={4} bg={useColorModeValue('gray.100', 'gray.800')}>
          <ResourceDropdown onSelect={handleResourceSelect} />
          <Button onClick={() => setShowMetrics(!showMetrics)} size="sm">
            {showMetrics ? 'Hide Metrics' : 'Show CPU Metrics'}
          </Button>
        </Flex>

        {showMetrics && (
          <Box p={4}>
            <MetricsPanel />
          </Box>
        )}

        <ChatWindow
          messages={messages}
          input={input}
          onInputChange={setInput}
          onSend={sendMessage}
          isResponding={isLoading}
          onStop={() => setIsLoading(false)}
        />

        <Container maxW="container.lg" py={4}>
          <Flex gap={2}>
            <Input
              placeholder="Type your query..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') sendMessage();
              }}
              isDisabled={isLoading}
            />
            <Button onClick={isLoading ? () => setIsLoading(false) : sendMessage}>
              {isLoading ? <FiSquare /> : <FiSend />}
            </Button>
          </Flex>
          {isLoading && <LoadingDots />}
        </Container>

        <ResourceModal
          isOpen={modal.isOpen}
          onClose={modal.onClose}
          resource={resourceType}
          data={resourceData}
        />
      </Flex>
    </Flex>
  );
};

export default App;
