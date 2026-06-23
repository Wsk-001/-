"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Prompt } from "@/lib/types";
import { api } from "@/lib/api";
import { extractVariables } from "@/lib/utils";
import PromptListComp from "@/components/studio/PromptList";
import PromptEditor from "@/components/studio/PromptEditor";
import VarInjector from "@/components/studio/VarInjector";
import DryRunPanel from "@/components/studio/DryRunPanel";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

export default function StudioPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [showNewPrompt, setShowNewPrompt] = useState(false);
  const [newPromptName, setNewPromptName] = useState("");
  const [newPromptCategory, setNewPromptCategory] = useState("general");

  const [varValues, setVarValues] = useState<Record<string, string>>({});
  const [dryRunResult, setDryRunResult] = useState<{
    output: string;
    tokens_used: number;
  } | null>(null);
  const [dryRunLoading, setDryRunLoading] = useState(false);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getPrompts();
      setPrompts(data);
      if (data.length > 0 && !selectedPrompt) {
        setSelectedPrompt(data[0]);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompts");
    } finally {
      setLoading(false);
    }
  }, [selectedPrompt]);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  const handleSelectPrompt = async (id: string) => {
    try {
      const prompt = prompts.find((p) => p.id === id) || (await api.getPrompts()).find((p) => p.id === id);
      if (prompt) {
        setSelectedPrompt(prompt);
        setVarValues({});
        setDryRunResult(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompt");
    }
  };

  const handlePromptChange = (field: string, value: string) => {
    if (!selectedPrompt) return;
    const updated = { ...selectedPrompt, [field]: value };
    if (field === "content") {
      updated.variables = extractVariables(value);
    }
    setSelectedPrompt(updated);
  };

  const handleSave = async () => {
    if (!selectedPrompt) return;
    try {
      setSaving(true);
      const updated = await api.updatePrompt(selectedPrompt.id, {
        name: selectedPrompt.name,
        category: selectedPrompt.category,
        content: selectedPrompt.content,
      });
      setSelectedPrompt(updated);
      setPrompts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save prompt");
    } finally {
      setSaving(false);
    }
  };

  const handleCreatePrompt = async () => {
    if (!newPromptName) return;
    try {
      const prompt = await api.createPrompt({
        name: newPromptName,
        category: newPromptCategory,
        content: "",
        variables: [],
      });
      setPrompts((prev) => [...prev, prompt]);
      setSelectedPrompt(prompt);
      setShowNewPrompt(false);
      setNewPromptName("");
      setNewPromptCategory("general");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create prompt");
    }
  };

  const handleVarValueChange = (variable: string, value: string) => {
    setVarValues((prev) => ({ ...prev, [variable]: value }));
  };

  const handleDryRun = async () => {
    if (!selectedPrompt) return;
    try {
      setDryRunLoading(true);
      const result = await api.dryRunPrompt(selectedPrompt.id, {
        variables: varValues,
      });
      setDryRunResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry run failed");
    } finally {
      setDryRunLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      <PromptListComp
        prompts={prompts}
        selectedId={selectedPrompt?.id || null}
        onSelect={handleSelectPrompt}
        onCreate={() => setShowNewPrompt(true)}
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {selectedPrompt ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-100">
                {selectedPrompt.name}
              </h2>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
            </div>

            <PromptEditor
              prompt={selectedPrompt}
              onChange={handlePromptChange}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <VarInjector
                variables={selectedPrompt.variables}
                values={varValues}
                onValueChange={handleVarValueChange}
              />
              <DryRunPanel
                result={dryRunResult}
                loading={dryRunLoading}
                onRun={handleDryRun}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-500">
              Select a prompt from the left or create a new one
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={showNewPrompt}
        onClose={() => setShowNewPrompt(false)}
        title="Create New Prompt"
      >
        <div className="space-y-4">
          <Input
            label="Prompt Name"
            placeholder="Enter prompt name..."
            value={newPromptName}
            onChange={(e) => setNewPromptName(e.target.value)}
          />
          <Input
            label="Category"
            placeholder="e.g., writing, analysis..."
            value={newPromptCategory}
            onChange={(e) => setNewPromptCategory(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowNewPrompt(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreatePrompt} disabled={!newPromptName}>
              Create Prompt
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
