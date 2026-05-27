"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { LeadDetailDrawer } from "./LeadDetailDrawer";
import type { B2BProfilePack } from "@/lib/b2b-profile-packs";
import type { Lead, LeadDetail } from "@/lib/types";

interface LeadTableProps {
  /**
   * Optional list of leads to render. When omitted, the table
   * falls back to an empty list when omitted
   * keep working without code changes.
   */
  leads?: Lead[];
  /**
   * Resolver that returns a full `LeadDetail` for a given lead id.
   * In API mode this reads from the already-loaded enriched batch
   * (no extra fetch). When omitted, the drawer uses its built-in
   * mock fallback path.
   */
  getLeadDetail?: (leadId: string) => LeadDetail | null;
  profilePack?: B2BProfilePack;
}

type PriorityFilter = "All" | "High" | "Medium" | "Low";
type StatusFilter = "All" | "Pending" | "Approved" | "Rejected";

function getFitScoreStyles(score: number) {
  if (score >= 80) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (score >= 50) return "bg-amber-50 text-amber-700 border border-amber-200";
  return "bg-slate-100 text-slate-600 border border-slate-200";
}

function getStatusDotColor(status: Lead["status"]) {
  switch (status) {
    case "Approved":
      return "bg-[--color-success]";
    case "Rejected":
      return "bg-[--color-error]";
    case "Needs Edit":
      return "bg-[--color-warning]";
    case "Pending Review":
    default:
      return "bg-[--accent-primary]";
  }
}

function getPriorityStyles(priority: Lead["priority"]) {
  switch (priority) {
    case "High":
      return "bg-[--color-success-bg] text-[--color-success]";
    case "Medium":
      return "bg-[--color-warning-bg] text-[--color-warning]";
    case "Low":
      return "bg-[--bg-overlay] text-[--text-muted]";
  }
}

function getStatusStyles(status: Lead["status"]) {
  switch (status) {
    case "Approved":
      return "text-[--color-success]";
    case "Rejected":
      return "text-[--color-error]";
    case "Needs Edit":
      return "text-[--color-warning]";
    case "Pending Review":
    default:
      return "text-[--accent-primary]";
  }
}

export function LeadTable({
  leads: leadsProp,
  getLeadDetail,
  profilePack,
}: LeadTableProps = {}) {
  const initialLeads = leadsProp ?? [];
  const [leads, setLeads] = useState<Lead[]>(initialLeads);
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("All");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<LeadDetail | null>(null);

  // Keep local state in sync when the prop changes (e.g. after a
  // mock → api swap or a refresh in API mode). Filters / search /
  // human-review status edits are intentionally preserved across
  // these updates by re-applying overrides keyed on lead id.
  useEffect(() => {
    if (leadsProp === undefined) return;
    setLeads((prev) => {
      const overrides = new Map(prev.map((l) => [l.id, l.status] as const));
      return leadsProp.map((l) => ({
        ...l,
        status: overrides.get(l.id) ?? l.status,
      }));
    });
  }, [leadsProp]);

  const filteredLeads = useMemo(() => {
    return leads
      .filter((lead) => {
        if (priorityFilter !== "All" && lead.priority !== priorityFilter) return false;
        if (statusFilter !== "All") {
          if (statusFilter === "Pending" && lead.status !== "Pending Review") return false;
          if (statusFilter === "Approved" && lead.status !== "Approved") return false;
          if (statusFilter === "Rejected" && lead.status !== "Rejected") return false;
        }
        if (searchQuery && !lead.company.toLowerCase().includes(searchQuery.toLowerCase())) {
          return false;
        }
        return true;
      })
      .sort((a, b) => b.fit_score - a.fit_score);
  }, [leads, priorityFilter, statusFilter, searchQuery]);

  const handleRowClick = (lead: Lead) => {
    setSelectedLead(lead);
    setSelectedDetail(getLeadDetail ? getLeadDetail(lead.id) : null);
    setIsDrawerOpen(true);
  };

  const handleStatusChange = (leadId: string, status: Lead["status"]) => {
    setLeads((prev) =>
      prev.map((lead) => (lead.id === leadId ? { ...lead, status } : lead))
    );
    if (selectedLead?.id === leadId) {
      setSelectedLead((prev) => (prev ? { ...prev, status } : null));
    }
  };

  const priorityOptions: PriorityFilter[] = ["All", "High", "Medium", "Low"];
  const statusOptions: StatusFilter[] = ["All", "Pending", "Approved", "Rejected"];

  return (
    <div>
      {/* Table Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-[--text-primary]">Results</h2>
          <p className="text-sm text-[--text-muted]">{filteredLeads.length} leads processed</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Priority Filter */}
          <div className="flex items-center rounded-lg border border-[--border-default] p-1">
            {priorityOptions.map((option) => (
              <button
                key={option}
                onClick={() => setPriorityFilter(option)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  priorityFilter === option
                    ? "bg-[--accent-primary] text-white"
                    : "text-[--text-secondary] hover:text-[--text-primary]"
                }`}
              >
                {option}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <div className="flex items-center rounded-lg border border-[--border-default] p-1">
            {statusOptions.map((option) => (
              <button
                key={option}
                onClick={() => setStatusFilter(option)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  statusFilter === option
                    ? "bg-[--accent-primary] text-white"
                    : "text-[--text-secondary] hover:text-[--text-primary]"
                }`}
              >
                {option}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[--text-muted]" />
            <Input
              placeholder="Search company..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-8 w-48 bg-transparent border-[--border-default] text-sm"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="border border-[--border-default] rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-[--surface] border-b-2 border-[--border-default] hover:bg-[--surface]">
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Company</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Industry</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Country</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Contact Role</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Fit Score</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Priority</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">QA</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Status</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Est. Cost</TableHead>
              <TableHead className="py-3 px-4 text-[--text-muted] text-xs font-medium">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLeads.map((lead, index) => (
              <TableRow
                key={lead.id}
                onClick={() => handleRowClick(lead)}
                className={`cursor-pointer hover:bg-[#f8fafc] border-b border-[--border-subtle] ${
                  index % 2 === 0 ? "bg-[--bg-elevated]" : "bg-[--background]"
                }`}
              >
                <TableCell className="py-3 px-4 text-sm text-[--text-primary] font-medium">
                  {lead.company}
                </TableCell>
                <TableCell className="py-3 px-4 text-sm text-[--text-secondary]">{lead.industry}</TableCell>
                <TableCell className="py-3 px-4 text-sm text-[--text-secondary]">{lead.country}</TableCell>
                <TableCell className="py-3 px-4 text-sm text-[--text-secondary]">{lead.contact_role}</TableCell>
                <TableCell className="py-3 px-4">
                  <span className={`inline-flex items-center justify-center min-w-[2.5rem] h-7 px-2 rounded-md text-xs font-semibold font-mono ${getFitScoreStyles(lead.fit_score)}`}>
                    {lead.fit_score}
                  </span>
                </TableCell>
                <TableCell className="py-3 px-4">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityStyles(lead.priority)}`}>
                    {lead.priority}
                  </span>
                </TableCell>
                <TableCell className="py-3 px-4 text-sm font-mono text-[--text-secondary]">{lead.qa_score}</TableCell>
                <TableCell className="py-3 px-4">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${getStatusStyles(lead.status)}`}>
                    <span
                      className={`w-1.5 h-1.5 rounded-full shrink-0 ${getStatusDotColor(lead.status)}`}
                      aria-hidden
                    />
                    {lead.status}
                  </span>
                </TableCell>
                <TableCell className="py-3 px-4 text-sm font-mono text-[--text-muted]">{lead.est_cost}</TableCell>
                <TableCell>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRowClick(lead);
                    }}
                    className="text-sm text-[--accent-primary] hover:underline"
                  >
                    View Details
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Lead Detail Drawer */}
      <LeadDetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        lead={selectedLead}
        detail={selectedDetail}
        onStatusChange={handleStatusChange}
        profilePack={profilePack}
      />
    </div>
  );
}
