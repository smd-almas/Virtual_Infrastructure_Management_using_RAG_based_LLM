// src/utils/formatters.ts

export function formatTimestamp(isoString: string): string {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

// src/utils/formatters.ts
export const getPreview = (text: string): string => {
  const words = text.trim().split(/\s+/);
  if (words.length >= 5) return words.slice(0, 5).join(" ");
  if (words.length >= 4) return words.slice(0, 4).join(" ");
  return words.slice(0, 3).join(" ");
};

  