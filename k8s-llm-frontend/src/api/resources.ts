// src/api/resources.ts
import client from './client';

export const getPods = () => client.get('/pods');
export const getDeployments = () => client.get('/deployments');
export const getServices = () => client.get('/services');
export const getConfigMaps = () => client.get('/configmaps');
export const getNamespaces = () => client.get('/namespaces');
export const getNodes = () => client.get('/nodes');
