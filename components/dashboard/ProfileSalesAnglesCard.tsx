"use client";

import type { B2BProfilePack } from "@/lib/b2b-profile-packs";

interface ProfileSalesAnglesCardProps {
  pack: B2BProfilePack;
}

/** Compact sidebar-style hints for lead detail — no drawer restructure. */
export function ProfileSalesAnglesCard({ pack }: ProfileSalesAnglesCardProps) {
  return (
    <section className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-3">
        Sales angle hints · {pack.displayName}
      </h3>
      <ul className="space-y-2">
        {pack.salesAngles.map((angle) => (
          <li key={angle} className="text-xs text-[--text-secondary] leading-relaxed">
            {angle}
          </li>
        ))}
      </ul>
    </section>
  );
}
