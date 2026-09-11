import React from 'react';
import { 
  Sparkles, 
  Layers, 
  Edit3, 
  Trash2, 
  ArrowUpRight, 
  Clock
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Design, DesignStatus } from '../../types/design';

interface DesignCardProps {
  design: Design;
  onView: (design: Design) => void;
  onEdit: (design: Design) => void;
  onDelete: (design: Design) => void;
}

const getStatusBadge = (status: DesignStatus) => {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Ready</Badge>;
    case 'rendering':
      return (
        <Badge variant="gold" className="animate-pulse">
          <Sparkles className="w-3 h-3 mr-1" />
          Rendering
        </Badge>
      );
    case 'rendered':
      return (
        <Badge variant="gold">
          <Sparkles className="w-3 h-3 mr-1" />
          Rendered
        </Badge>
      );
    case 'archived':
      return <Badge variant="secondary">Archived</Badge>;
    case 'draft':
    default:
      return <Badge variant="outline">Draft</Badge>;
  }
};

export const DesignCard: React.FC<DesignCardProps> = ({
  design,
  onView,
  onEdit,
  onDelete,
}) => {
  const formattedDate = new Date(design.updated_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Card className="bg-[#0E111A]/90 border-white/[0.07] hover:border-amber-400/30 transition-all duration-300 group flex flex-col justify-between overflow-hidden shadow-xl hover:shadow-2xl">
      <div>
        {/* Visual Header / Image Frame */}
        <div 
          onClick={() => onView(design)}
          className="relative h-48 sm:h-52 w-full bg-[#080A10] flex items-center justify-center cursor-pointer overflow-hidden border-b border-white/[0.06] transition-colors duration-300"
        >
          {design.rendered_image_url ? (
            <img
              src={design.rendered_image_url}
              alt={design.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
            />
          ) : design.sketch_image_url ? (
            <img
              src={design.sketch_image_url}
              alt={design.name}
              className="w-full h-full object-contain p-4 group-hover:scale-105 transition-transform duration-500 ease-out filter invert opacity-85"
            />
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2 text-slate-600 group-hover:text-amber-300/70 transition-colors">
              <div className="p-3 rounded-2xl bg-[#121622] border border-white/5">
                <Layers className="w-7 h-7" />
              </div>
              <span className="text-[10px] font-medium tracking-wider uppercase">
                {design.category} Blueprint
              </span>
            </div>
          )}

          {/* Category Pill Over Image */}
          <div className="absolute top-3 left-3">
            <span className="px-2.5 py-1 rounded-lg bg-[#080A10]/80 backdrop-blur-md border border-white/10 text-[10px] font-semibold text-amber-200 shadow-sm tracking-wide">
              {design.category}
            </span>
          </div>

          {/* Status Badge Over Image */}
          <div className="absolute top-3 right-3">
            {getStatusBadge(design.status)}
          </div>
        </div>

        <CardHeader className="p-5 pb-2 space-y-1.5">
          <CardTitle 
            onClick={() => onView(design)}
            className="text-base font-serif font-medium text-white group-hover:text-amber-200 transition-colors cursor-pointer line-clamp-1"
          >
            {design.name}
          </CardTitle>
          <CardDescription className="text-xs text-slate-400 font-light line-clamp-2 min-h-[32px] leading-relaxed">
            {design.description || 'No extended crafting notes provided.'}
          </CardDescription>
        </CardHeader>
      </div>

      <div className="p-5 pt-0 space-y-4">
        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-white/5 font-light">
          <span className="flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-slate-500" />
            {formattedDate}
          </span>
          {design.ai_prompt && (
            <span className="flex items-center gap-1 text-amber-300/80 font-medium" title="AI Prompt Configured">
              <Sparkles className="w-3 h-3 text-amber-300" />
              Prompt Ready
            </span>
          )}
        </div>

        <CardFooter className="p-0 flex items-center justify-between gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onView(design)}
            className="flex-1 h-8 text-xs font-semibold text-slate-200 hover:text-white bg-[#121622] hover:bg-[#181E2E] border-white/5"
          >
            <span>View Design</span>
            <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(design)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-amber-300 hover:border-amber-400/40 border-white/10"
            title="Edit Design"
            aria-label="Edit Design"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(design)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-rose-300 hover:border-rose-500/40 border-white/10"
            title="Delete Design"
            aria-label="Delete Design"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </CardFooter>
      </div>
    </Card>
  );
};
