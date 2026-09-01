import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  Sliders,
  Info,
  Layers,
  ChevronRight
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Slider } from '../ui/slider';
import { Tooltip } from '../ui/tooltip';

interface Message {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  timestamp: string;
}

interface DesignChatPanelProps {
  initialPrompt?: string;
  onPromptChange?: (prompt: string) => void;
  canvasInfluence: number;
  onCanvasInfluenceChange: (influence: number) => void;
  designName?: string;
  designCategory?: string;
}

const PROMPT_SUGGESTIONS = [
  'A modern solitaire ring with tapered baguette diamonds in platinum',
  'Art Deco emerald pendant with intricate filigree in 18k yellow gold',
  'Vintage floral necklace with Akoya pearls and ruby gemstone accents',
  'Geometric cuff bracelet with pavé-set diamonds and satin gold finish',
];

export const DesignChatPanel: React.FC<DesignChatPanelProps> = ({
  initialPrompt = '',
  onPromptChange,
  canvasInfluence,
  onCanvasInfluenceChange,
  designName,
  designCategory,
}) => {
  const [prompt, setPrompt] = useState<string>(initialPrompt);
  const [generationMode, setGenerationMode] = useState<'classic' | 'premium'>('premium');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'ai',
      text: `Hello Artisan! I'm your JewelMind creative copilot. Draw on the sketch canvas, customize your gemstones and precious metal specifications below, or choose a prompt suggestion to prepare for photorealistic AI rendering.`,
      timestamp: 'Just now',
    },
  ]);

  const handleSendPrompt = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim()) return;

    const userText = prompt.trim();
    const newMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [
      ...prev,
      newMsg,
      {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: `Prompt staged for ${designCategory || 'Jewellery'} design "${designName || 'Untitled'}". When you click "Save Sketch", this generative prompt and your sketch blueprint will be synced for Phase 7 GPU diffusion inference.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);

    if (onPromptChange) {
      onPromptChange(userText);
    }
  };

  const handleApplySuggestion = (suggestion: string) => {
    setPrompt(suggestion);
    if (onPromptChange) {
      onPromptChange(suggestion);
    }
  };

  return (
    <div className="w-full h-full bg-[#0a0d14] border-l border-slate-800/90 flex flex-col justify-between select-none text-slate-200">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-slate-800/90 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-tight">AI Design Studio</div>
            <div className="text-[10px] text-slate-400">Sketch Conditioning & Prompts</div>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Active</span>
        </div>
      </div>

      {/* Message Conversation Stream */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-1`}
          >
            <div
              className={`p-3 rounded-2xl text-xs leading-relaxed max-w-[90%] ${
                msg.sender === 'user'
                  ? 'bg-amber-500 text-slate-950 font-medium rounded-tr-sm'
                  : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-sm shadow-sm'
              }`}
            >
              {msg.text}
            </div>
            <span className="text-[10px] text-slate-500 px-1">{msg.timestamp}</span>
          </div>
        ))}
      </div>

      {/* Bottom Control & Composer Section */}
      <div className="p-3.5 border-t border-slate-800/90 bg-slate-950/60 space-y-3.5">
        {/* Prompt Suggestions */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            <span>Prompt Suggestions</span>
            <Sparkles className="w-3 h-3 text-amber-400" />
          </div>
          <div className="flex flex-col space-y-1.5 max-h-28 overflow-y-auto pr-1">
            {PROMPT_SUGGESTIONS.map((sug, i) => (
              <button
                key={i}
                onClick={() => handleApplySuggestion(sug)}
                className="text-left px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800/80 hover:border-amber-500/40 hover:bg-slate-800/60 transition text-[11px] text-slate-300 flex items-center justify-between group"
              >
                <span className="truncate pr-2">{sug}</span>
                <ChevronRight className="w-3 h-3 text-slate-500 group-hover:text-amber-400 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Prompt Composer */}
        <form onSubmit={handleSendPrompt} className="space-y-2">
          <div className="relative">
            <Textarea
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                if (onPromptChange) onPromptChange(e.target.value);
              }}
              placeholder="Ask or describe precious metal, gemstones, carat, polish..."
              className="w-full bg-[#0d121f] border-slate-800 text-xs text-white placeholder:text-slate-500 resize-none min-h-[64px] max-h-[120px] rounded-xl pr-10 focus:border-amber-400"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendPrompt();
                }
              }}
            />
            <Button
              type="submit"
              size="icon"
              variant="gold"
              className="absolute right-2 bottom-2 h-7 w-7 rounded-lg shadow"
              disabled={!prompt.trim()}
              aria-label="Send Prompt"
            >
              <Send className="w-3.5 h-3.5" />
            </Button>
          </div>

          {/* Mode Pills & Canvas Influence */}
          <div className="space-y-2.5 pt-1">
            {/* Mode selection pills */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <button
                  type="button"
                  onClick={() => setGenerationMode('classic')}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                    generationMode === 'classic'
                      ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40'
                      : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
                  }`}
                >
                  Classic
                </button>
                <button
                  type="button"
                  onClick={() => setGenerationMode('premium')}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                    generationMode === 'premium'
                      ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40'
                      : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
                  }`}
                >
                  Premium Ultra
                </button>
              </div>

              <div className="flex items-center space-x-1 text-[10px] text-slate-400">
                <Layers className="w-3 h-3 text-amber-400" />
                <span>Diffusion v2</span>
              </div>
            </div>

            {/* Canvas Influence Slider */}
            <div className="space-y-1 pt-1">
              <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                <div className="flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-amber-400" />
                  <span>Canvas Influence</span>
                  <Tooltip content="Controls how strictly the AI photorealistic diffusion model follows your sketch lines">
                    <Info className="w-3 h-3 text-slate-500 cursor-help" />
                  </Tooltip>
                </div>
                <span className="font-mono text-amber-400">{canvasInfluence}%</span>
              </div>
              <Slider
                value={canvasInfluence}
                min={0}
                max={100}
                step={5}
                onValueChange={onCanvasInfluenceChange}
              />
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
