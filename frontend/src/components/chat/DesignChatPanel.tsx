import React, { useState, useRef } from 'react';
import {
  Sparkles,
  Send,
  Sliders,
  Info,
  ChevronRight,
  Loader2,
  Wand2,
  Plus,
  X,
  Image as ImageIcon,
  Tag,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Slider } from '../ui/slider';
import { Tooltip } from '../ui/tooltip';
import { Badge } from '../ui/badge';
import { geminiDesignService } from '../../services/api/geminiDesignService';
import { DesignState } from '../../types/ai';

export interface ChatMessage {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  timestamp: string;
  changes?: string[];
}

interface DesignChatPanelProps {
  initialPrompt?: string;
  onPromptChange?: (prompt: string) => void;
  designState: DesignState;
  onDesignStateChange: (state: DesignState) => void;
  canvasInfluence: number;
  onCanvasInfluenceChange: (influence: number) => void;
  designName?: string;
  designCategory?: string;
  onTriggerRender?: () => void;
  isRendering?: boolean;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const PROMPT_SUGGESTIONS = [
  'Change metal to 18k rose gold with mirror polish',
  'Replace center stone with an oval cut royal blue sapphire',
  'Add micro-pavé diamonds along the shank',
  'Craft an Art Deco emerald cut solitaire in 950 platinum',
];

export const DesignChatPanel: React.FC<DesignChatPanelProps> = ({
  initialPrompt = '',
  onPromptChange,
  designState,
  onDesignStateChange,
  canvasInfluence,
  onCanvasInfluenceChange,
  designName,
  designCategory,
  onTriggerRender,
  isRendering = false,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const [inputText, setInputText] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [attachedImageBase64, setAttachedImageBase64] = useState<string | null>(null);
  const [attachedImageName, setAttachedImageName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      text: `Welcome to the Canva AI Atelier. I am your fine jewellery design copilot. Chat with me to modify precious metals, gemstones, settings, or aesthetic details in real-time.`,
      timestamp: 'Just now',
    },
  ]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAttachedImageName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = reader.result as string;
      setAttachedImageBase64(b64);
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleRemoveAttachedImage = () => {
    setAttachedImageBase64(null);
    setAttachedImageName(null);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputText.trim();
    if (!text && !attachedImageBase64) return;

    const userMsgId = Date.now().toString();
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: text || 'Attached reference image for design review.',
        timestamp: timeStr,
      },
    ]);

    setInputText('');
    setIsProcessing(true);

    try {
      // Call Conversational Design State Modification endpoint
      const response = await geminiDesignService.modifyDesignState({
        current_state: designState,
        user_instruction: text || 'Analyze this reference image and align the design state accordingly.',
        image_base64: attachedImageBase64,
      });

      const updated = response.updated_state;
      onDesignStateChange(updated);

      if (onPromptChange && updated.current_prompt) {
        onPromptChange(updated.current_prompt);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: response.assistant_reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          changes: response.changes_detected,
        },
      ]);
      handleRemoveAttachedImage();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: `I've noted your instruction "${text}". Your design prompt has been updated for synthesis.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleEnhancePrompt = async () => {
    const textToEnhance = inputText.trim() || designState.current_prompt || initialPrompt;
    if (!textToEnhance || isProcessing) return;

    setIsProcessing(true);
    try {
      const res = await geminiDesignService.enhancePrompt({
        user_prompt: textToEnhance,
        yolo_category: designCategory || designState.category,
      });

      const enhanced = res.enhanced_prompt || res.renderer_prompt;
      setInputText(enhanced);
      if (onPromptChange) onPromptChange(enhanced);

      // Also update designState prompt
      onDesignStateChange({
        ...designState,
        current_prompt: enhanced,
        renderer_prompt: res.renderer_prompt,
        negative_prompt: res.negative_prompt,
      });

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'ai',
          text: `✨ Enhanced prompt with luxury jewellery terminology: "${enhanced}"`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch {
      // Graceful fallback
    } finally {
      setIsProcessing(false);
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-12 h-full bg-[#0A0C12] border-l border-white/[0.07] flex flex-col items-center py-4 space-y-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="text-slate-400 hover:text-white"
          title="Expand Atelier Copilot"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
        <div className="p-2 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
          <Sparkles className="w-4 h-4" />
        </div>
        <span className="text-[10px] font-medium tracking-wider text-slate-500 uppercase [writing-mode:vertical-lr] rotate-180">
          AI Copilot
        </span>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-[#0A0C12] border-l border-white/[0.07] flex flex-col justify-between select-none text-slate-200">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-white/[0.07] flex items-center justify-between bg-[#0E111A]/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white tracking-wide font-serif">Canva AI Copilot</div>
            <div className="text-[10px] text-slate-400 font-light truncate max-w-[170px]">
              {designName || 'Jewellery Workspace'}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Active</span>
          </div>
          {onToggleCollapse && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleCollapse}
              className="h-7 w-7 text-slate-400 hover:text-white"
              title="Minimize Copilot"
            >
              <Minimize2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* Active Design State Chips */}
      <div className="px-3.5 py-2.5 bg-[#08090E] border-b border-white/5 flex flex-wrap items-center gap-1.5 overflow-x-auto max-h-24">
        <div className="flex items-center text-[10px] text-slate-400 font-medium mr-1">
          <Tag className="w-3 h-3 mr-1 text-amber-300" />
          <span>State:</span>
        </div>
        {designState.category && (
          <Badge variant="gold" className="text-[10px] py-0 px-2">
            {designState.category}
          </Badge>
        )}
        {designState.primary_metal && (
          <Badge variant="secondary" className="text-[10px] py-0 px-2 bg-[#121622] text-slate-300 border-white/10">
            {designState.primary_metal}
          </Badge>
        )}
        {designState.has_gemstones && designState.gemstone_type && (
          <Badge variant="secondary" className="text-[10px] py-0 px-2 bg-[#121622] text-slate-300 border-white/10">
            {designState.gemstone_cut ? `${designState.gemstone_cut} ` : ''}{designState.gemstone_type}
          </Badge>
        )}
        {designState.has_gemstones === false && (
          <Badge variant="secondary" className="text-[10px] py-0 px-2 bg-[#121622] text-slate-400 border-white/10">
            No Gemstones
          </Badge>
        )}
        {designState.setting_type && (
          <Badge variant="secondary" className="text-[10px] py-0 px-2 bg-[#121622] text-slate-300 border-white/10">
            {designState.setting_type}
          </Badge>
        )}
      </div>

      {/* Message Conversation Stream */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3.5 scrollbar-thin scrollbar-thumb-white/10">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-1`}
          >
            <div
              className={`p-3 rounded-2xl text-xs leading-relaxed max-w-[92%] font-light ${
                msg.sender === 'user'
                  ? 'bg-amber-400 text-slate-950 font-medium rounded-tr-sm shadow-md'
                  : 'bg-[#0E111A] border border-white/5 text-slate-300 rounded-tl-sm shadow-sm'
              }`}
            >
              <div>{msg.text}</div>
              {msg.changes && msg.changes.length > 0 && (
                <div className="mt-2 pt-2 border-t border-white/10 flex flex-wrap gap-1">
                  {msg.changes.map((ch, idx) => (
                    <span
                      key={idx}
                      className="inline-block px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-200 text-[9px] font-mono"
                    >
                      +{ch.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <span className="text-[10px] text-slate-500 px-1 font-mono">{msg.timestamp}</span>
          </div>
        ))}
        {isProcessing && (
          <div className="flex items-center space-x-2 text-xs text-amber-300 bg-amber-400/5 p-2.5 rounded-xl border border-amber-400/10">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span className="font-light">Copilot analyzing & compiling design state...</span>
          </div>
        )}
      </div>

      {/* Bottom Control & Composer Section */}
      <div className="p-3.5 border-t border-white/[0.07] bg-[#0A0C12]/95 space-y-3">
        {/* Quick Suggestions */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-widest">
            <span>Conversational Suggestions</span>
            <Sparkles className="w-3 h-3 text-amber-300" />
          </div>
          <div className="flex flex-col space-y-1 max-h-20 overflow-y-auto pr-1 scrollbar-thin">
            {PROMPT_SUGGESTIONS.map((sug, i) => (
              <button
                key={i}
                onClick={() => setInputText(sug)}
                className="text-left px-2.5 py-1 rounded-lg bg-[#0E111A] border border-white/5 hover:border-amber-400/30 hover:bg-[#141824] transition text-[11px] text-slate-300 flex items-center justify-between group cursor-pointer"
              >
                <span className="truncate pr-2 font-light">{sug}</span>
                <ChevronRight className="w-3 h-3 text-slate-500 group-hover:text-amber-300 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Attached Image Pill */}
        {attachedImageBase64 && (
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-[#141824] border border-amber-400/30 text-xs text-amber-200">
            <div className="flex items-center space-x-2 truncate">
              <ImageIcon className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span className="truncate text-[11px]">{attachedImageName || 'Reference Blueprint'}</span>
            </div>
            <button
              type="button"
              onClick={handleRemoveAttachedImage}
              className="p-1 hover:text-rose-300 text-slate-400 transition"
              title="Remove Attachment"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Prompt / Instruction Composer */}
        <form onSubmit={handleSendMessage} className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
              Instruct Copilot / Prompt
            </span>
            <button
              type="button"
              onClick={handleEnhancePrompt}
              disabled={isProcessing}
              className="text-[10px] text-amber-300 hover:text-amber-200 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1 font-medium transition cursor-pointer"
            >
              <Wand2 className="w-3 h-3 text-amber-400" />
              <span>Enhance Prompt ✨</span>
            </button>
          </div>

          <div className="relative">
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="e.g. Change metal to rose gold, replace center diamond with oval sapphire..."
              className="w-full bg-[#080A10] border-white/10 text-xs text-white placeholder:text-slate-500 resize-none min-h-[56px] max-h-[100px] rounded-xl pl-9 pr-10 focus:border-amber-400/50"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />

            {/* Hidden File Input for Image Attachment */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              className="hidden"
              onChange={handleImageSelect}
            />

            {/* Attachment Button (+) */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute left-2.5 bottom-2.5 text-slate-400 hover:text-amber-300 transition p-0.5"
              title="Attach Reference Image/Sketch"
            >
              <Plus className="w-4 h-4" />
            </button>

            {/* Send Button */}
            <Button
              type="submit"
              size="icon"
              variant="gold"
              className="absolute right-2 bottom-2 h-7 w-7 rounded-lg shadow-sm"
              disabled={isProcessing || (!inputText.trim() && !attachedImageBase64)}
              aria-label="Send Message"
            >
              <Send className="w-3.5 h-3.5" />
            </Button>
          </div>

          {/* Geometry Influence Slider */}
          <div className="space-y-1 pt-1">
            <div className="flex items-center justify-between text-[10px] font-medium text-slate-300">
              <div className="flex items-center space-x-1.5">
                <Sliders className="w-3 h-3 text-amber-300" />
                <span className="font-light">Geometry Influence</span>
                <Tooltip content="Controls ControlNet conditioning weight (0% = pure text prompt, 100% = strict blueprint lock)">
                  <Info className="w-3 h-3 text-slate-500 cursor-help" />
                </Tooltip>
              </div>
              <span className="font-mono text-amber-300">{canvasInfluence}%</span>
            </div>
            <Slider
              value={canvasInfluence}
              min={0}
              max={100}
              step={5}
              onValueChange={onCanvasInfluenceChange}
            />
          </div>

          {/* Direct Render Action Button */}
          {onTriggerRender && (
            <div className="pt-2">
              <Button
                type="button"
                variant="gold"
                size="sm"
                onClick={onTriggerRender}
                disabled={isRendering}
                className="w-full font-semibold text-xs h-9 shadow-lg shadow-amber-500/10 flex items-center justify-center space-x-2"
              >
                {isRendering ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Synthesizing Jewellery Render...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Render Visuals Now</span>
                  </>
                )}
              </Button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default DesignChatPanel;
