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
    <Card className="bg-[#0b0f19] border-slate-800 hover:border-amber-500/40 transition duration-200 group flex flex-col justify-between overflow-hidden shadow-lg hover:shadow-amber-500/5">
      <div>
        {/* Visual Header / Thumbnail Placeholder */}
        <div 
          onClick={() => onView(design)}
          className="relative h-44 w-full bg-gradient-to-br from-slate-900 via-[#0d1222] to-slate-950 flex items-center justify-center cursor-pointer overflow-hidden border-b border-slate-800/80 group-hover:from-slate-900 group-hover:to-[#111728] transition"
        >
          {design.rendered_image_url ? (
            <img
              src={design.rendered_image_url}
              alt={design.name}
              className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            />
          ) : design.sketch_image_url ? (
            <img
              src={design.sketch_image_url}
              alt={design.name}
              className="w-full h-full object-contain p-4 group-hover:scale-105 transition duration-300 filter invert opacity-80"
            />
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2 text-slate-600 group-hover:text-amber-400/70 transition">
              <div className="p-3 rounded-2xl bg-slate-800/60 border border-slate-700/50">
                <Layers className="w-8 h-8" />
              </div>
              <span className="text-[11px] font-medium tracking-wide uppercase">
                {design.category} Design
              </span>
            </div>
          )}

          {/* Category Pill Over Image */}
          <div className="absolute top-3 left-3">
            <span className="px-2.5 py-1 rounded-md bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-[11px] font-semibold text-amber-300 shadow-sm">
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
            className="text-base font-bold text-white group-hover:text-amber-300 transition cursor-pointer line-clamp-1"
          >
            {design.name}
          </CardTitle>
          <CardDescription className="text-xs text-slate-400 line-clamp-2 min-h-[32px]">
            {design.description || 'No description provided for this jewellery design.'}
          </CardDescription>
        </CardHeader>
      </div>

      <div className="p-5 pt-0 space-y-4">
        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Updated {formattedDate}
          </span>
          {design.ai_prompt && (
            <span className="flex items-center gap-1 text-amber-400/80" title="AI Prompt Configured">
              <Sparkles className="w-3 h-3" />
              Prompt Ready
            </span>
          )}
        </div>

        <CardFooter className="p-0 flex items-center justify-between gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onView(design)}
            className="flex-1 h-8 text-xs font-semibold text-slate-200 hover:text-white"
          >
            <span>View</span>
            <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(design)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-amber-300 hover:border-amber-400/50"
            title="Edit Design"
            aria-label="Edit Design"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(design)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400 hover:border-rose-500/50"
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
