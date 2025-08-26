// src/components/ResourceDropdown.tsx
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';

const resourceOptions = [
  'Pods',
  'Deployments',
  'Services',
  'ConfigMaps',
  'Namespaces',
  'Nodes',
];

interface ResourceDropdownProps {
  onSelect: (resource: string) => void;
}

const ResourceDropdown = ({ onSelect }: ResourceDropdownProps) => {
  return (
    <Menu>
      <MenuButton as={Button} rightIcon={<ChevronDownIcon />} colorScheme="teal">
        Resources
      </MenuButton>
      <MenuList>
        {resourceOptions.map((resource) => (
          <MenuItem key={resource} onClick={() => onSelect(resource)}>
            {resource}
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  );
};

export default ResourceDropdown;
