"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Pipeline, PipelineStep } from "@/lib/types";
import { api } from "@/lib/api";
import PipelineListComp from "@/components/builder/PipelineList";
import StepCard from "@/components/builder/StepCard";
import StepConfigPanel from "@/components/builder/StepConfigPanel";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Card, { CardContent } from "@/components/ui/Card";

export default function BuilderPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configStep, setConfigStep] = useState<PipelineStep | null>(null);
  const [showNewPipeline, setShowNewPipeline] = useState(false);
  const [showAddStep, setShowAddStep] = useState(false);

  const [newPipelineName, setNewPipelineName] = useState("");
  const [newPipelineDesc, setNewPipelineDesc] = useState("");

  const [newStepName, setNewStepName] = useState("");
  const [newStepType, setNewStepType] = useState("source_collector");

  const fetchPipelines = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getPipelines();
      setPipelines(data);
      if (data.length > 0 && !selectedPipeline) {
        setSelectedPipeline(data[0]);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipelines");
    } finally {
      setLoading(false);
    }
  }, [selectedPipeline]);

  useEffect(() => {
    fetchPipelines();
  }, [fetchPipelines]);

  const handleSelectPipeline = async (id: string) => {
    try {
      const pipeline = await api.getPipeline(id);
      setSelectedPipeline(pipeline);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipeline");
    }
  };

  const handleCreatePipeline = async () => {
    if (!newPipelineName) return;
    try {
      const pipeline = await api.createPipeline({
        name: newPipelineName,
        description: newPipelineDesc,
        steps: [],
      });
      setPipelines((prev) => [...prev, pipeline]);
      setSelectedPipeline(pipeline);
      setShowNewPipeline(false);
      setNewPipelineName("");
      setNewPipelineDesc("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create pipeline");
    }
  };

  const handleToggleStep = async (stepKey: string) => {
    if (!selectedPipeline) return;
    const step = selectedPipeline.steps.find((s) => s.key === stepKey);
    if (!step) return;
    try {
      const updated = await api.updateStep(selectedPipeline.id, stepKey, {
        ...step,
        enabled: !step.enabled,
      });
      setSelectedPipeline(updated);
      setPipelines((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle step");
    }
  };

  const handleConfigStep = (stepKey: string) => {
    const step = selectedPipeline?.steps.find((s) => s.key === stepKey);
    if (step) setConfigStep(step);
  };

  const handleSaveStepConfig = async (stepKey: string, config: Record<string, unknown>) => {
    if (!selectedPipeline) return;
    try {
      const updated = await api.updateStep(selectedPipeline.id, stepKey, config);
      setSelectedPipeline(updated);
      setPipelines((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save step config");
    }
  };

  const handleDeleteStep = async (stepKey: string) => {
    if (!selectedPipeline) return;
    try {
      const updated = await api.deleteStep(selectedPipeline.id, stepKey);
      setSelectedPipeline(updated);
      setPipelines((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete step");
    }
  };

  const handleAddStep = async () => {
    if (!selectedPipeline || !newStepName) return;
    try {
      const updated = await api.addStep(selectedPipeline.id, {
        key: newStepName.toLowerCase().replace(/\s+/g, "_"),
        name: newStepName,
        type: newStepType,
        enabled: true,
        order: selectedPipeline.steps.length,
        config: {},
      });
      setSelectedPipeline(updated);
      setPipelines((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setShowAddStep(false);
      setNewStepName("");
      setNewStepType("source_collector");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add step");
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
      <PipelineListComp
        pipelines={pipelines}
        selectedId={selectedPipeline?.id || null}
        onSelect={handleSelectPipeline}
        onCreate={() => setShowNewPipeline(true)}
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {selectedPipeline ? (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-100">
                  {selectedPipeline.name}
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  {selectedPipeline.description || "No description"}
                </p>
              </div>
              <Button onClick={() => setShowAddStep(true)}>+ Add Step</Button>
            </div>

            <div className="space-y-2">
              {selectedPipeline.steps.length === 0 ? (
                <Card>
                  <CardContent>
                    <div className="text-center py-8">
                      <p className="text-slate-500 text-sm mb-3">
                        No steps in this pipeline yet
                      </p>
                      <Button size="sm" onClick={() => setShowAddStep(true)}>
                        Add First Step
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                [...selectedPipeline.steps]
                  .sort((a, b) => a.order - b.order)
                  .map((step) => (
                    <StepCard
                      key={step.key}
                      step={step}
                      onToggle={handleToggleStep}
                      onConfig={handleConfigStep}
                      onDelete={handleDeleteStep}
                    />
                  ))
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-500">
              Select a pipeline from the left or create a new one
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={showNewPipeline}
        onClose={() => setShowNewPipeline(false)}
        title="Create New Pipeline"
      >
        <div className="space-y-4">
          <Input
            label="Pipeline Name"
            placeholder="Enter pipeline name..."
            value={newPipelineName}
            onChange={(e) => setNewPipelineName(e.target.value)}
          />
          <Input
            label="Description"
            placeholder="Enter description..."
            value={newPipelineDesc}
            onChange={(e) => setNewPipelineDesc(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowNewPipeline(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreatePipeline} disabled={!newPipelineName}>
              Create Pipeline
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={showAddStep}
        onClose={() => setShowAddStep(false)}
        title="Add Step"
      >
        <div className="space-y-4">
          <Input
            label="Step Name"
            placeholder="Enter step name..."
            value={newStepName}
            onChange={(e) => setNewStepName(e.target.value)}
          />
          <select
            value={newStepType}
            onChange={(e) => setNewStepType(e.target.value)}
            className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="source_collector">Source Collector</option>
            <option value="content_analyzer">Content Analyzer</option>
            <option value="outline_generator">Outline Generator</option>
            <option value="article_writer">Article Writer</option>
            <option value="image_generator">Image Generator</option>
            <option value="reviewer">Reviewer</option>
            <option value="formatter">Formatter</option>
            <option value="publisher">Publisher</option>
          </select>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowAddStep(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddStep} disabled={!newStepName}>
              Add Step
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={!!configStep}
        onClose={() => setConfigStep(null)}
        title={`Configure: ${configStep?.name || ""}`}
      >
        {configStep && (
          <StepConfigPanel
            step={configStep}
            onSave={handleSaveStepConfig}
            onClose={() => setConfigStep(null)}
          />
        )}
      </Modal>
    </div>
  );
}
