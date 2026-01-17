'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Link2,
  Bell,
  FileText,
  AlertTriangle,
  Users,
  X,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Suggestion {
  title: string;
  description: string;
  type: 'connect' | 'remind' | 'document' | 'alert' | 'share';
  relevance: number;
  related_items: string[];
}

const TYPE_CONFIG = {
  connect: {
    icon: Link2,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    label: 'Connection',
  },
  remind: {
    icon: Bell,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    label: 'Reminder',
  },
  document: {
    icon: FileText,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    label: 'Document',
  },
  alert: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    label: 'Alert',
  },
  share: {
    icon: Users,
    color: 'text-pink-400',
    bg: 'bg-pink-500/10',
    border: 'border-pink-500/20',
    label: 'Share',
  },
};

function SuggestionCard({
  suggestion,
  index,
  onDismiss,
}: {
  suggestion: Suggestion;
  index: number;
  onDismiss: () => void;
}) {
  const config = TYPE_CONFIG[suggestion.type] || TYPE_CONFIG.document;
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: -20, scale: 0.95 }}
      transition={{ delay: index * 0.1 }}
      className={`relative rounded-lg border ${config.border} ${config.bg} p-4 group`}
    >
      <button
        onClick={onDismiss}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-white/10 rounded"
      >
        <X className="w-3 h-3 text-zinc-500" />
      </button>

      <div className="flex gap-3">
        <div className={`p-2 rounded-lg ${config.bg} shrink-0`}>
          <Icon className={`w-4 h-4 ${config.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-medium text-white truncate">{suggestion.title}</h4>
            <Badge variant="outline" className={`text-[10px] ${config.color} ${config.border}`}>
              {config.label}
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 line-clamp-2">{suggestion.description}</p>

          {/* Relevance indicator */}
          <div className="flex items-center gap-2 mt-2">
            <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${suggestion.relevance * 10}%` }}
                transition={{ delay: index * 0.1 + 0.3, duration: 0.5 }}
                className={`h-full ${config.bg.replace('/10', '/50')}`}
                style={{ backgroundColor: config.color.replace('text-', '').replace('-400', '') }}
              />
            </div>
            <span className="text-[10px] text-zinc-500">{suggestion.relevance}/10</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

interface SuggestionsPanelProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function SuggestionsPanel({ collapsed = false, onToggle }: SuggestionsPanelProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSuggestions = async () => {
    try {
      setRefreshing(true);
      const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
      const response = await fetch(`${apiUrl}/suggestions?limit=5`);

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
    // Refresh suggestions every 5 minutes
    const interval = setInterval(fetchSuggestions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const dismissSuggestion = (index: number) => {
    setSuggestions((prev) => prev.filter((_, i) => i !== index));
  };

  if (collapsed) {
    return (
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={onToggle}
        className="fixed bottom-4 right-4 z-50 p-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg hover:shadow-purple-500/25 transition-shadow"
      >
        <Sparkles className="w-5 h-5" />
        {suggestions.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
            {suggestions.length}
          </span>
        )}
      </motion.button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="w-80 border-l border-zinc-800 bg-zinc-900/50 backdrop-blur flex flex-col h-full"
    >
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-white">AI Suggestions</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={fetchSuggestions}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 text-zinc-400 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
          {onToggle && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onToggle}>
              <ChevronRight className="w-4 h-4 text-zinc-400" />
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 rounded-lg bg-zinc-800/50 animate-pulse" />
            ))}
          </div>
        ) : suggestions.length === 0 ? (
          <div className="text-center py-8">
            <Sparkles className="w-12 h-12 mx-auto mb-4 text-zinc-700" />
            <p className="text-zinc-500 text-sm">No suggestions right now</p>
            <p className="text-zinc-600 text-xs mt-1">Keep working and I'll find helpful insights</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="space-y-3">
              {suggestions.map((suggestion, index) => (
                <SuggestionCard
                  key={`${suggestion.title}-${index}`}
                  suggestion={suggestion}
                  index={index}
                  onDismiss={() => dismissSuggestion(index)}
                />
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-800">
        <p className="text-xs text-zinc-500 text-center">
          Suggestions refresh every 5 minutes
        </p>
      </div>
    </motion.div>
  );
}

// Floating suggestions widget for main page
export function SuggestionsWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const response = await fetch(`${apiUrl}/suggestions?limit=3`);
        if (response.ok) {
          const data = await response.json();
          setSuggestions(data.suggestions || []);
        }
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
      }
    };

    fetchSuggestions();
  }, []);

  return (
    <>
      {/* Floating button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg hover:shadow-purple-500/30 transition-all"
      >
        <Sparkles className="w-6 h-6" />
        {suggestions.length > 0 && !isOpen && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-500 text-white text-xs font-bold flex items-center justify-center"
          >
            {suggestions.length}
          </motion.span>
        )}
      </motion.button>

      {/* Popup panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-50 w-80 rounded-xl border border-zinc-800 bg-zinc-900/95 backdrop-blur shadow-2xl"
          >
            <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span className="font-medium text-white">AI Suggestions</span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-zinc-800 rounded"
              >
                <X className="w-4 h-4 text-zinc-500" />
              </button>
            </div>
            <div className="p-4 max-h-80 overflow-y-auto space-y-3">
              {suggestions.length === 0 ? (
                <p className="text-zinc-500 text-sm text-center py-4">
                  No suggestions yet
                </p>
              ) : (
                suggestions.map((suggestion, index) => (
                  <SuggestionCard
                    key={`${suggestion.title}-${index}`}
                    suggestion={suggestion}
                    index={index}
                    onDismiss={() => setSuggestions(prev => prev.filter((_, i) => i !== index))}
                  />
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
