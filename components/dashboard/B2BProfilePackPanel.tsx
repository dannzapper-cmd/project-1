"use client";

import { useId } from "react";
import { Lightbulb } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  B2B_PROFILE_PACKS,
  DEFAULT_PROFILE_PACK_ID,
  HONEST_FRAMING_NOTE,
  getProfilePack,
  suggestProfileFromIndustries,
  type B2BProfilePack,
  type B2BProfilePackId,
} from "@/lib/b2b-profile-packs";

interface B2BProfilePackPanelProps {
  selectedId: B2BProfilePackId;
  onSelect: (id: B2BProfilePackId) => void;
  /** Lead industries from the current batch (for auto-suggest hint only). */
  batchIndustries?: string[];
}

export function B2BProfilePackPanel({
  selectedId,
  onSelect,
  batchIndustries = [],
}: B2BProfilePackPanelProps) {
  const selectId = useId();
  const pack: B2BProfilePack = getProfilePack(selectedId);
  const suggestedId = suggestProfileFromIndustries(batchIndustries);
  const showSuggestion =
    suggestedId !== null && suggestedId !== selectedId;

  return (
    <section
      aria-labelledby="b2b-profile-pack-heading"
      className="bg-[--bg-surface] border border-[--border-default] rounded-lg p-5 space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2
            id="b2b-profile-pack-heading"
            className="text-sm font-semibold text-[--text-primary]"
          >
            B2B profile pack
          </h2>
          <p className="text-xs text-[--text-muted] mt-0.5">
            Adjusts review framing — scoring logic is unchanged
          </p>
        </div>
        <div className="flex flex-col gap-1 sm:items-end">
          <label htmlFor={selectId} className="sr-only">
            Select B2B profile pack
          </label>
          <Select value={selectedId} onValueChange={(v) => onSelect(v as B2BProfilePackId)}>
            <SelectTrigger
              id={selectId}
              size="sm"
              className="w-full sm:w-[280px] border-[--border-default] bg-[--bg-elevated] text-[--text-primary]"
            >
              <SelectValue placeholder="Select profile" />
            </SelectTrigger>
            <SelectContent className="bg-[--bg-elevated] border-[--border-default]">
              {B2B_PROFILE_PACKS.map((p) => (
                <SelectItem key={p.id} value={p.id} className="text-[--text-primary]">
                  {p.displayName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {showSuggestion && suggestedId && (
        <p className="text-xs text-[--accent-secondary] flex items-start gap-2 bg-[--accent-primary]/10 border border-[--accent-primary]/20 rounded-lg px-3 py-2">
          <Lightbulb className="h-3.5 w-3.5 shrink-0 mt-0.5" aria-hidden />
          <span>
            Your batch is mostly{" "}
            <span className="font-medium">{getProfilePack(suggestedId).displayName}</span>
            {" "}— consider switching if that matches your ICP.
          </span>
        </p>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-[--text-primary]">{pack.displayName}</p>
          <p className="text-xs text-[--text-secondary]">{pack.description}</p>
          <p className="text-xs text-[--text-muted]">
            Target user: <span className="text-[--text-secondary]">{pack.targetUser}</span>
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wider text-[--text-muted] mb-2">
            What this profile prioritizes
          </p>
          <ul className="space-y-1">
            {pack.priorities.map((item) => (
              <li key={item} className="text-xs text-[--text-secondary] flex gap-2">
                <span className="text-[--accent-primary]">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p
        role="note"
        className="text-xs text-[--text-muted] border-t border-[--border-subtle] pt-3"
      >
        {HONEST_FRAMING_NOTE}
      </p>
    </section>
  );
}

export { DEFAULT_PROFILE_PACK_ID };
