import React, { useState, useEffect } from 'react';
import {
  X,
  Sparkles,
  ShieldCheck,
  Save,
  CheckCircle2,
  AlertTriangle,
  Plus,
  Trash2,
  Loader2,
  Lock,
  Layers,
  Clock,
  Gem,
  Scale,
  Hammer,
  HelpCircle,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  productionSpecificationService,
  ProductionSpecificationResponse,
  ProductionMaterialUpdate,
  ProductionGemstoneUpdate,
  ProductionStepUpdate,
  ProductionSpecificationUpdateRequest,
} from '../../services/api/productionSpecificationService';

interface ProductionSpecificationReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  specificationId?: string | null;
  renderId?: string | null;
  renderThumbnailUrl?: string | null;
  renderVersion?: number | null;
  designCategory?: string | null;
  onSpecificationApproved?: (spec: ProductionSpecificationResponse) => void;
}

export const ProductionSpecificationReviewModal: React.FC<ProductionSpecificationReviewModalProps> = ({
  isOpen,
  onClose,
  specificationId,
  renderId,
  renderThumbnailUrl,
  renderVersion,
  designCategory,
  onSpecificationApproved,
}) => {
  const [specification, setSpecification] = useState<ProductionSpecificationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [approving, setApproving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showApproveConfirm, setShowApproveConfirm] = useState<boolean>(false);

  // Form states
  const [category, setCategory] = useState<string>('');
  const [roughWeight, setRoughWeight] = useState<number | ''>('');
  const [finishedWeight, setFinishedWeight] = useState<number | ''>('');
  const [complexity, setComplexity] = useState<string>('moderate');
  const [notes, setNotes] = useState<string>('');
  const [materials, setMaterials] = useState<ProductionMaterialUpdate[]>([]);
  const [materialOrigins, setMaterialOrigins] = useState<Record<number, string>>({});
  const [gemstones, setGemstones] = useState<ProductionGemstoneUpdate[]>([]);
  const [gemstoneOrigins, setGemstoneOrigins] = useState<Record<number, string>>({});
  const [steps, setSteps] = useState<ProductionStepUpdate[]>([]);
  const [stepOrigins, setStepOrigins] = useState<Record<number, string>>({});

  // Active specification load effect
  useEffect(() => {
    if (!isOpen) return;

    const fetchSpecification = async () => {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
        let spec: ProductionSpecificationResponse | null = null;
        if (specificationId) {
          spec = await productionSpecificationService.getSpecification(specificationId);
        } else if (renderId) {
          const list = await productionSpecificationService.getSpecificationsByRender(renderId);
          if (list.length > 0) {
            spec = list[0]; // newest
          } else {
            // If no spec exists yet, generate one
            spec = await productionSpecificationService.generateSpecification({ render_id: renderId });
          }
        }

        if (spec) {
          populateForm(spec);
        } else {
          setError('No production specification found for this render.');
        }
      } catch (err: any) {
        console.error('Failed to load production specification:', err);
        setError(err?.message || 'Failed to load production specification');
      } finally {
        setLoading(false);
      }
    };

    fetchSpecification();
  }, [isOpen, specificationId, renderId]);

  const populateForm = (spec: ProductionSpecificationResponse) => {
    setSpecification(spec);
    setCategory(spec.category || designCategory || 'ring');
    setRoughWeight(spec.estimated_rough_metal_weight_grams ?? '');
    setFinishedWeight(spec.estimated_finished_metal_weight_grams ?? '');
    setComplexity(spec.complexity_rating || 'moderate');
    setNotes(spec.fabrication_notes || '');

    // Materials
    setMaterials(
      spec.materials.map((m) => ({
        id: m.id,
        metal_type: m.metal_type,
        metal_purity: m.metal_purity,
        metal_color: m.metal_color,
        metal_finish: m.metal_finish,
        plating: m.plating,
        estimated_weight_grams: m.estimated_weight_grams,
        casting_loss_percentage: m.casting_loss_percentage,
      }))
    );
    const mOrigins: Record<number, string> = {};
    spec.materials.forEach((m, idx) => {
      mOrigins[idx] = m.origin;
    });
    setMaterialOrigins(mOrigins);

    // Gemstones
    setGemstones(
      spec.gemstones.map((g) => ({
        id: g.id,
        gemstone_type: g.gemstone_type,
        cut_shape: g.cut_shape,
        stone_count: g.stone_count,
        estimated_carat_weight: g.estimated_carat_weight,
        approximate_dimensions_mm: g.approximate_dimensions_mm,
        setting_type: g.setting_type,
        is_center_stone: g.is_center_stone,
      }))
    );
    const gOrigins: Record<number, string> = {};
    spec.gemstones.forEach((g, idx) => {
      gOrigins[idx] = g.origin;
    });
    setGemstoneOrigins(gOrigins);

    // Routing Steps
    setSteps(
      spec.steps.map((s) => ({
        id: s.id,
        step_number: s.step_number,
        stage_name: s.stage_name,
        required_skill: s.required_skill,
        required_machine_type: s.required_machine_type,
        base_hours: s.base_hours,
        per_unit_hours: s.per_unit_hours,
        description: s.description,
        quality_checkpoint: s.quality_checkpoint,
      }))
    );
    const sOrigins: Record<number, string> = {};
    spec.steps.forEach((s, idx) => {
      sOrigins[idx] = s.origin;
    });
    setStepOrigins(sOrigins);
  };

  const isApproved = specification?.status === 'approved';

  // Materials handlers
  const handleAddMaterial = () => {
    setMaterials([
      ...materials,
      {
        metal_type: 'gold',
        metal_purity: '18k',
        metal_color: 'yellow',
        metal_finish: 'high_polish',
        plating: null,
        estimated_weight_grams: 4.5,
        casting_loss_percentage: 10.0,
      },
    ]);
  };

  const handleUpdateMaterial = (index: number, field: keyof ProductionMaterialUpdate, value: any) => {
    const updated = [...materials];
    updated[index] = { ...updated[index], [field]: value };
    setMaterials(updated);
  };

  const handleRemoveMaterial = (index: number) => {
    setMaterials(materials.filter((_, i) => i !== index));
  };

  // Gemstones handlers
  const handleAddGemstone = () => {
    setGemstones([
      ...gemstones,
      {
        gemstone_type: 'diamond',
        cut_shape: 'round_brilliant',
        stone_count: 1,
        estimated_carat_weight: 1.0,
        approximate_dimensions_mm: '6.5mm',
        setting_type: 'prong',
        is_center_stone: true,
      },
    ]);
  };

  const handleUpdateGemstone = (index: number, field: keyof ProductionGemstoneUpdate, value: any) => {
    const updated = [...gemstones];
    updated[index] = { ...updated[index], [field]: value };
    setGemstones(updated);
  };

  const handleRemoveGemstone = (index: number) => {
    setGemstones(gemstones.filter((_, i) => i !== index));
  };

  // Routing Steps handlers
  const handleAddStep = () => {
    const nextStepNum = steps.length > 0 ? Math.max(...steps.map((s) => s.step_number)) + 1 : 1;
    setSteps([
      ...steps,
      {
        step_number: nextStepNum,
        stage_name: 'Hand Polishing',
        required_skill: 'polisher',
        required_machine_type: 'polishing_lathe',
        base_hours: 1.5,
        per_unit_hours: 0.5,
        description: 'Surface finishing and high-luster buffing.',
        quality_checkpoint: 'Mirror finish free of swirl marks.',
      },
    ]);
  };

  const handleUpdateStep = (index: number, field: keyof ProductionStepUpdate, value: any) => {
    const updated = [...steps];
    updated[index] = { ...updated[index], [field]: value };
    setSteps(updated);
  };

  const handleRemoveStep = (index: number) => {
    const filtered = steps.filter((_, i) => i !== index);
    // Renumber sequentially
    const renumbered = filtered.map((s, idx) => ({ ...s, step_number: idx + 1 }));
    setSteps(renumbered);
  };

  // Build Payload
  const buildPayload = (): ProductionSpecificationUpdateRequest => {
    return {
      category: category || undefined,
      estimated_rough_metal_weight_grams: roughWeight === '' ? null : Number(roughWeight),
      estimated_finished_metal_weight_grams: finishedWeight === '' ? null : Number(finishedWeight),
      total_gemstone_count: gemstones.reduce((sum, g) => sum + (g.stone_count || 0), 0),
      complexity_rating: complexity,
      fabrication_notes: notes || undefined,
      materials: materials.map((m) => ({
        id: m.id || null,
        metal_type: m.metal_type,
        metal_purity: m.metal_purity,
        metal_color: m.metal_color || null,
        metal_finish: m.metal_finish || null,
        plating: m.plating || null,
        estimated_weight_grams: m.estimated_weight_grams ? Number(m.estimated_weight_grams) : null,
        casting_loss_percentage: m.casting_loss_percentage ? Number(m.casting_loss_percentage) : 10.0,
      })),
      gemstones: gemstones.map((g) => ({
        id: g.id || null,
        gemstone_type: g.gemstone_type,
        cut_shape: g.cut_shape || null,
        stone_count: Number(g.stone_count || 0),
        estimated_carat_weight: g.estimated_carat_weight ? Number(g.estimated_carat_weight) : null,
        approximate_dimensions_mm: g.approximate_dimensions_mm || null,
        setting_type: g.setting_type || null,
        is_center_stone: Boolean(g.is_center_stone),
      })),
      steps: steps.map((s) => ({
        id: s.id || null,
        step_number: Number(s.step_number),
        stage_name: s.stage_name,
        required_skill: s.required_skill,
        required_machine_type: s.required_machine_type || null,
        base_hours: Number(s.base_hours || 0),
        per_unit_hours: Number(s.per_unit_hours || 0),
        description: s.description || null,
        quality_checkpoint: s.quality_checkpoint || null,
      })),
    };
  };

  // Save changes
  const handleSave = async () => {
    if (!specification) return;
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const payload = buildPayload();
      const updated = await productionSpecificationService.updateSpecification(specification.id, payload);
      populateForm(updated);
      setSuccessMessage('Artisan modifications saved successfully.');
    } catch (err: any) {
      console.error('Failed to save specification:', err);
      setError(err?.message || 'Failed to save specification changes');
    } finally {
      setSaving(false);
    }
  };

  // Approve specification
  const handleApprove = async () => {
    if (!specification) return;

    // Client-side quick checks
    if (materials.length === 0) {
      setError('Cannot approve: At least one material is required in the Bill of Materials.');
      return;
    }
    if (steps.length === 0) {
      setError('Cannot approve: At least one manufacturing routing stage is required.');
      return;
    }

    setApproving(true);
    setError(null);
    setShowApproveConfirm(false);

    try {
      // If dirty, save first
      const payload = buildPayload();
      await productionSpecificationService.updateSpecification(specification.id, payload);

      // Now approve
      const approved = await productionSpecificationService.approveSpecification(specification.id);
      populateForm(approved);
      setSuccessMessage('Specification approved and permanently locked for manufacturing.');
      if (onSpecificationApproved) {
        onSpecificationApproved(approved);
      }
    } catch (err: any) {
      console.error('Failed to approve specification:', err);
      setError(err?.message || 'Failed to approve specification');
    } finally {
      setApproving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      data-testid="production-specification-modal"
    >
      <div className="relative w-full max-w-5xl max-h-[90vh] flex flex-col bg-[#0D111A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden text-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#121622]">
          <div className="flex items-center space-x-3">
            {renderThumbnailUrl && (
              <img
                src={renderThumbnailUrl}
                alt="Source Render"
                className="w-12 h-12 rounded-lg object-cover border border-white/10"
              />
            )}
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-semibold tracking-wide text-white">
                  Artisan Production Specification Review
                </h2>
                <Badge variant={isApproved ? 'success' : 'default'} data-testid="specification-status-badge">
                  {isApproved ? 'Approved' : 'Draft'}
                </Badge>
                {specification && (
                  <span className="text-xs text-slate-400 font-mono">
                    Spec V{specification.version_number} &bull; Render V{renderVersion || specification.render_id.slice(0, 4)}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Authoritative manufacturing Bill of Materials & workshop routing blueprint
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {specification?.ai_confidence_score && (
              <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/10 text-xs text-slate-300">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>AI Confidence: {Math.round(specification.ai_confidence_score * 100)}%</span>
              </div>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
              aria-label="Close review modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* AI Disclaimer Banner */}
        <div className="px-6 py-2.5 bg-amber-400/[0.06] border-b border-amber-400/20 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center space-x-2">
            <HelpCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              {isApproved
                ? 'This specification has been verified by the master artisan and is locked for manufacturing.'
                : 'AI-generated manufacturing estimate. Artisan review and approval are required before casting or workshop routing.'}
            </span>
          </div>
          {isApproved && specification?.approved_at && (
            <div className="flex items-center space-x-1 text-slate-400 font-mono text-[11px]">
              <Lock className="w-3 h-3 text-emerald-400" />
              <span>Approved {new Date(specification.approved_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMessage && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
              <p className="text-xs text-slate-400">Loading production blueprint...</p>
            </div>
          ) : (
            <>
              {/* Overview Metrics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Scale className="w-3.5 h-3.5 text-amber-400" />
                    <span>Finished Weight</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      disabled={isApproved}
                      value={finishedWeight}
                      onChange={(e) => setFinishedWeight(e.target.value === '' ? '' : Number(e.target.value))}
                      className="w-20 px-2 py-0.5 bg-black/40 border border-white/10 rounded text-sm font-semibold text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                    />
                    <span className="text-xs text-slate-400">g</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Scale className="w-3.5 h-3.5 text-slate-400" />
                    <span>Rough Casting</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      disabled={isApproved}
                      value={roughWeight}
                      onChange={(e) => setRoughWeight(e.target.value === '' ? '' : Number(e.target.value))}
                      className="w-20 px-2 py-0.5 bg-black/40 border border-white/10 rounded text-sm font-semibold text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                    />
                    <span className="text-xs text-slate-400">g</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Gem className="w-3.5 h-3.5 text-blue-400" />
                    <span>Total Gemstones</span>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {gemstones.reduce((sum, g) => sum + (g.stone_count || 0), 0)} stones
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Total Bench Hours</span>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {steps.reduce((sum, s) => sum + (s.base_hours || 0) + (s.per_unit_hours || 0), 0).toFixed(1)} hrs
                  </p>
                </div>
              </div>

              {/* General Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/5">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Jewellery Category</label>
                  <input
                    type="text"
                    disabled={isApproved}
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75"
                    placeholder="ring, necklace, earrings, etc."
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Complexity Rating</label>
                  <select
                    disabled={isApproved}
                    value={complexity}
                    onChange={(e) => setComplexity(e.target.value)}
                    className="w-full px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75"
                  >
                    <option value="simple">Simple (Solitaire / Band)</option>
                    <option value="moderate">Moderate (Pavé / Halo)</option>
                    <option value="intricate">Intricate (Filigree / Multi-stone)</option>
                    <option value="masterpiece">Masterpiece (Haute Joaillerie)</option>
                  </select>
                </div>
              </div>

              {/* Section 1: Materials BOM */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-semibold text-white">Metal Bill of Materials (BOM)</h3>
                  </div>
                  {!isApproved && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAddMaterial}
                      className="h-7 text-xs border-white/10 hover:border-amber-400/30"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Metal
                    </Button>
                  )}
                </div>

                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#121622] text-slate-400 border-b border-white/10">
                      <tr>
                        <th className="px-3 py-2 font-medium">Metal</th>
                        <th className="px-3 py-2 font-medium">Purity</th>
                        <th className="px-3 py-2 font-medium">Color</th>
                        <th className="px-3 py-2 font-medium">Finish</th>
                        <th className="px-3 py-2 font-medium">Est. Net (g)</th>
                        <th className="px-3 py-2 font-medium">Loss %</th>
                        <th className="px-3 py-2 font-medium">Origin</th>
                        {!isApproved && <th className="px-3 py-2 text-right">Action</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-[#0D111A]">
                      {materials.map((mat, idx) => (
                        <tr key={idx} className="hover:bg-white/[0.02]">
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={mat.metal_type}
                              onChange={(e) => handleUpdateMaterial(idx, 'metal_type', e.target.value)}
                              className="w-20 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={mat.metal_purity}
                              onChange={(e) => handleUpdateMaterial(idx, 'metal_purity', e.target.value)}
                              className="w-16 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={mat.metal_color || ''}
                              onChange={(e) => handleUpdateMaterial(idx, 'metal_color', e.target.value)}
                              className="w-18 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={mat.metal_finish || ''}
                              onChange={(e) => handleUpdateMaterial(idx, 'metal_finish', e.target.value)}
                              className="w-24 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              disabled={isApproved}
                              value={mat.estimated_weight_grams ?? ''}
                              onChange={(e) =>
                                handleUpdateMaterial(
                                  idx,
                                  'estimated_weight_grams',
                                  e.target.value === '' ? null : Number(e.target.value)
                                )
                              }
                              className="w-16 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="1"
                              min="0"
                              disabled={isApproved}
                              value={mat.casting_loss_percentage ?? 10}
                              onChange={(e) =>
                                handleUpdateMaterial(
                                  idx,
                                  'casting_loss_percentage',
                                  e.target.value === '' ? null : Number(e.target.value)
                                )
                              }
                              className="w-14 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-amber-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              variant={
                                materialOrigins[idx] === 'ARTISAN_OVERRIDE' || !mat.id
                                  ? 'gold'
                                  : 'secondary'
                              }
                              className="text-[9px] py-0 px-1.5"
                            >
                              {materialOrigins[idx] === 'ARTISAN_OVERRIDE' || !mat.id
                                ? 'Artisan Override'
                                : 'AI Estimate'}
                            </Badge>
                          </td>
                          {!isApproved && (
                            <td className="px-3 py-2 text-right">
                              <button
                                onClick={() => handleRemoveMaterial(idx)}
                                className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                                title="Remove line item"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 2: Gemstones Requirements */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Gem className="w-4 h-4 text-blue-400" />
                    <h3 className="text-sm font-semibold text-white">Gemstones Requirements</h3>
                    <span className="text-[11px] text-slate-400 font-normal">
                      (Optional for gemstone-free designs)
                    </span>
                  </div>
                  {!isApproved && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAddGemstone}
                      className="h-7 text-xs border-white/10 hover:border-blue-400/30"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Gemstone
                    </Button>
                  )}
                </div>

                {gemstones.length === 0 ? (
                  <div className="p-4 rounded-xl border border-dashed border-white/10 text-center text-xs text-slate-400 bg-white/[0.01]">
                    No gemstones configured (plain metal jewellery piece).
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-white/10">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-[#121622] text-slate-400 border-b border-white/10">
                        <tr>
                          <th className="px-3 py-2 font-medium">Type</th>
                          <th className="px-3 py-2 font-medium">Cut / Shape</th>
                          <th className="px-3 py-2 font-medium">Count</th>
                          <th className="px-3 py-2 font-medium">Carats</th>
                          <th className="px-3 py-2 font-medium">Dimensions</th>
                          <th className="px-3 py-2 font-medium">Setting</th>
                          <th className="px-3 py-2 font-medium text-center">Center?</th>
                          <th className="px-3 py-2 font-medium">Origin</th>
                          {!isApproved && <th className="px-3 py-2 text-right">Action</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5 bg-[#0D111A]">
                        {gemstones.map((gem, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="px-3 py-2">
                              <input
                                type="text"
                                disabled={isApproved}
                                value={gem.gemstone_type}
                                onChange={(e) => handleUpdateGemstone(idx, 'gemstone_type', e.target.value)}
                                className="w-24 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                type="text"
                                disabled={isApproved}
                                value={gem.cut_shape || ''}
                                onChange={(e) => handleUpdateGemstone(idx, 'cut_shape', e.target.value)}
                                className="w-24 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                type="number"
                                min="1"
                                disabled={isApproved}
                                value={gem.stone_count}
                                onChange={(e) =>
                                  handleUpdateGemstone(idx, 'stone_count', Number(e.target.value || 1))
                                }
                                className="w-14 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                disabled={isApproved}
                                value={gem.estimated_carat_weight ?? ''}
                                onChange={(e) =>
                                  handleUpdateGemstone(
                                    idx,
                                    'estimated_carat_weight',
                                    e.target.value === '' ? null : Number(e.target.value)
                                  )
                                }
                                className="w-16 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                type="text"
                                disabled={isApproved}
                                value={gem.approximate_dimensions_mm || ''}
                                onChange={(e) =>
                                  handleUpdateGemstone(idx, 'approximate_dimensions_mm', e.target.value)
                                }
                                className="w-20 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <input
                                type="text"
                                disabled={isApproved}
                                value={gem.setting_type || ''}
                                onChange={(e) => handleUpdateGemstone(idx, 'setting_type', e.target.value)}
                                className="w-20 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-blue-400/50 disabled:opacity-75 disabled:bg-transparent"
                              />
                            </td>
                            <td className="px-3 py-2 text-center">
                              <input
                                type="checkbox"
                                disabled={isApproved}
                                checked={gem.is_center_stone}
                                onChange={(e) => handleUpdateGemstone(idx, 'is_center_stone', e.target.checked)}
                                className="rounded bg-black/40 border-white/20 text-amber-400 focus:ring-0"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <Badge
                                variant={
                                  gemstoneOrigins[idx] === 'ARTISAN_OVERRIDE' || !gem.id
                                    ? 'gold'
                                    : 'secondary'
                                }
                                className="text-[9px] py-0 px-1.5"
                              >
                                {gemstoneOrigins[idx] === 'ARTISAN_OVERRIDE' || !gem.id
                                  ? 'Artisan Override'
                                  : 'AI Estimate'}
                              </Badge>
                            </td>
                            {!isApproved && (
                              <td className="px-3 py-2 text-right">
                                <button
                                  onClick={() => handleRemoveGemstone(idx)}
                                  className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                                  title="Remove gemstone line item"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Section 3: Manufacturing Routing */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Hammer className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-semibold text-white">Workshop Routing Stages</h3>
                  </div>
                  {!isApproved && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAddStep}
                      className="h-7 text-xs border-white/10 hover:border-emerald-400/30"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Stage
                    </Button>
                  )}
                </div>

                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#121622] text-slate-400 border-b border-white/10">
                      <tr>
                        <th className="px-2 py-2 text-center w-10">#</th>
                        <th className="px-3 py-2 font-medium">Stage Name</th>
                        <th className="px-3 py-2 font-medium">Skill</th>
                        <th className="px-3 py-2 font-medium">Machinery</th>
                        <th className="px-3 py-2 font-medium">Base (h)</th>
                        <th className="px-3 py-2 font-medium">Per Unit (h)</th>
                        <th className="px-3 py-2 font-medium">Quality Checkpoint</th>
                        <th className="px-3 py-2 font-medium">Origin</th>
                        {!isApproved && <th className="px-3 py-2 text-right">Action</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-[#0D111A]">
                      {steps.map((step, idx) => (
                        <tr key={idx} className="hover:bg-white/[0.02]">
                          <td className="px-2 py-2 text-center text-slate-400 font-mono font-semibold">
                            {step.step_number}
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={step.stage_name}
                              onChange={(e) => handleUpdateStep(idx, 'stage_name', e.target.value)}
                              className="w-32 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={step.required_skill}
                              onChange={(e) => handleUpdateStep(idx, 'required_skill', e.target.value)}
                              className="w-24 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={step.required_machine_type || ''}
                              onChange={(e) =>
                                handleUpdateStep(idx, 'required_machine_type', e.target.value)
                              }
                              className="w-24 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              disabled={isApproved}
                              value={step.base_hours}
                              onChange={(e) =>
                                handleUpdateStep(idx, 'base_hours', Number(e.target.value || 0))
                              }
                              className="w-14 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              disabled={isApproved}
                              value={step.per_unit_hours}
                              onChange={(e) =>
                                handleUpdateStep(idx, 'per_unit_hours', Number(e.target.value || 0))
                              }
                              className="w-14 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              disabled={isApproved}
                              value={step.quality_checkpoint || ''}
                              onChange={(e) =>
                                handleUpdateStep(idx, 'quality_checkpoint', e.target.value)
                              }
                              className="w-36 px-2 py-1 bg-black/40 border border-white/10 rounded text-xs text-white focus:outline-none focus:border-emerald-400/50 disabled:opacity-75 disabled:bg-transparent"
                              placeholder="Inspection criteria..."
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              variant={
                                stepOrigins[idx] === 'ARTISAN_OVERRIDE' || !step.id
                                  ? 'gold'
                                  : 'secondary'
                              }
                              className="text-[9px] py-0 px-1.5"
                            >
                              {stepOrigins[idx] === 'ARTISAN_OVERRIDE' || !step.id
                                ? 'Artisan Override'
                                : 'AI Estimate'}
                            </Badge>
                          </td>
                          {!isApproved && (
                            <td className="px-3 py-2 text-right">
                              <button
                                onClick={() => handleRemoveStep(idx)}
                                className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                                title="Remove routing stage"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 4: Fabrication Notes */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-white">
                  Atelier Fabrication Notes & Warnings
                </label>
                <textarea
                  disabled={isApproved}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400/50 disabled:opacity-75"
                  placeholder="Artisan instructions, casting notes, porosity warnings, assembly tips..."
                />
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-white/10 bg-[#121622] flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="border-white/10 text-xs hover:bg-white/5"
          >
            {isApproved ? 'Close' : 'Cancel'}
          </Button>

          {!isApproved && (
            <div className="flex items-center space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSave}
                disabled={saving || approving || loading}
                className="text-xs bg-[#1A2133] hover:bg-[#232D45] text-amber-300 border border-amber-400/20"
                data-testid="save-specification-btn"
              >
                {saving ? (
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                ) : (
                  <Save className="w-3.5 h-3.5 mr-1.5" />
                )}
                Save Overrides
              </Button>

              {showApproveConfirm ? (
                <div className="flex items-center space-x-1.5">
                  <span className="text-xs text-amber-300 font-medium">Confirm lock?</span>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="h-8 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
                    onClick={handleApprove}
                    disabled={approving}
                    data-testid="confirm-approve-specification-btn"
                  >
                    {approving ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    )}
                    Yes, Approve & Lock
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs border-white/10"
                    onClick={() => setShowApproveConfirm(false)}
                  >
                    No
                  </Button>
                </div>
              ) : (
                <Button
                  variant="gold"
                  size="sm"
                  onClick={() => setShowApproveConfirm(true)}
                  disabled={saving || approving || loading}
                  className="text-xs shadow-md"
                  data-testid="approve-specification-btn"
                >
                  <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
                  Approve Specification
                </Button>
              )}
            </div>
          )}

          {isApproved && (
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold">
              <Lock className="w-4 h-4" />
              <span>Specification Approved & Immutable</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
