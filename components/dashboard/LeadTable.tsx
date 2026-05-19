"use client";

import { useState, useMemo } from "react";
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
import { mockLeads } from "@/lib/mock-data";
import { LeadDetailDrawer } from "./LeadDetailDrawer";
import type { Lead } from "@/lib/types";

type PriorityFilter = "All" | "High" | "Medium" | "Low";
type StatusFilter = "All" | "Pending" | "Approved" | "Rejected";

function getFitScoreStyles(score: number) {
  if (score >= 70) return "bg-[--color-success-bg] text-[--color-success]";
  if (score >= 40) return "bg-[--color-warning-bg] text-[--color-warning]";
  return "bg-[--color-error-bg] text-[--color-error]";
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

export function LeadTable() {
  const [leads, setLeads] = useState<Lead[]>(mockLeads);
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("All");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

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
            <TableRow className="bg-[--bg-surface] border-b border-[--border-default] hover:bg-[--bg-surface]">
              <TableHead className="text-[--text-muted] text-xs font-medium">Company</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Industry</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Country</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Contact Role</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Fit Score</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Priority</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">QA</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Status</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Est. Cost</TableHead>
              <TableHead className="text-[--text-muted] text-xs font-medium">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLeads.map((lead) => (
              <TableRow
                key={lead.id}
                onClick={() => handleRowClick(lead)}
                className="cursor-pointer hover:bg-[--bg-overlay] border-b border-[--border-subtle]"
              >
                <TableCell className="text-sm text-[--text-primary] font-medium">
                  {lead.company}
                </TableCell>
                <TableCell className="text-sm text-[--text-secondary]">{lead.industry}</TableCell>
                <TableCell className="text-sm text-[--text-secondary]">{lead.country}</TableCell>
                <TableCell className="text-sm text-[--text-secondary]">{lead.contact_role}</TableCell>
                <TableCell>
                  <span className={`inline-flex items-center justify-center w-10 h-6 rounded text-xs font-semibold ${getFitScoreStyles(lead.fit_score)}`}>
                    {lead.fit_score}
                  </span>
                </TableCell>
                <TableCell>
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityStyles(lead.priority)}`}>
                    {lead.priority}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-[--text-secondary]">{lead.qa_score}</TableCell>
                <TableCell>
                  <span className={`text-sm font-medium ${getStatusStyles(lead.status)}`}>
                    {lead.status}
                  </span>
                </TableCell>
                <TableCell className="text-sm font-mono text-[--text-muted]">{lead.est_cost}</TableCell>
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
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
