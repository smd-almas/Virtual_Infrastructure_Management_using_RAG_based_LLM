import {
  Box,
  Heading,
  Select,
  Spinner,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import axios from "../api/client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

const metricOptions = [
  { label: "CPU Usage", value: "cpu" },
  { label: "Memory Usage", value: "memory" },
  { label: "Disk Usage", value: "disk" },
  { label: "Network RX", value: "net_rx" },
  { label: "Network TX", value: "net_tx" },
];

export default function MetricsPanel() {
  const [selectedMetric, setSelectedMetric] = useState("cpu");
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bg = useColorModeValue("gray.100", "gray.700");

  useEffect(() => {
    fetchMetricData();
    const interval = setInterval(fetchMetricData, 10000); // auto-refresh every 5s
    return () => clearInterval(interval);
  }, [selectedMetric]);

  const fetchMetricData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get("/metrics/time-series", {
        params: { metric_type: selectedMetric },
      });
      const raw = res.data?.metrics || [];

      // Format for Recharts: timestamp -> value
      const formatted = raw.map((point: any) => ({
        time: new Date(point.timestamp * 1000).toLocaleTimeString(),
        [selectedMetric]: point.value,
      }));

      setData(formatted);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load metrics");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={4} bg={bg} borderRadius="md" boxShadow="md" mt={4}>
      <Heading size="md" mb={2}>
        Resource Metrics
      </Heading>

      <Select
        mb={4}
        value={selectedMetric}
        onChange={(e) => setSelectedMetric(e.target.value)}
        width="200px"
      >
        {metricOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </Select>

      {loading ? (
        <Spinner />
      ) : error ? (
        <Text color="red.500">{error}</Text>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey={selectedMetric}
              stroke="#3182CE"
              strokeWidth={2}
              dot={false}
              isAnimationActive={true}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Box>
  );
}
