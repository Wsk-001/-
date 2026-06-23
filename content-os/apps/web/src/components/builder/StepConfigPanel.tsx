"use client";

import React, { useState } from "react";
import { PipelineStep } from "@/lib/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";

interface StepConfigPanelProps {
  step: PipelineStep;
  onSave: (stepKey: string, config: Record<string, unknown>) => void;
  onClose: () => void;
}

const stepTypes = [
  { value: "source_collector", label: "Source Collector" },
  { value: "content_analyzer", label: "Content Analyzer" },
  { value: "outline_generator", label: "Outline Generator" },
  { value: "article_writer", label: "Article Writer" },
  { value: "image_generator", label: "Image Generator" },
  { value: "reviewer", label: "Reviewer" },
  { value: "formatter", label: "Formatter" },
  { value: "publisher", label: "Publisher" },
];

export default function StepConfigPanel({ step, onSave, onClose }: StepConfigPanelProps) {
  const [name, setName] = useState(step.name);
  const [type, setType] = useState(step.type);
  const [configJson, setConfigJson] = useState(
    JSON.stringify(step.config, null, 2)
  );
  const [error, setError] = useState<string | null>(null);

  const handleSave = () => {
    try {
      const parsed = JSON.parse(configJson);
      onSave(step.key, { ...parsed, name, type });
      onClose();
    } catch {
      setError("Invalid JSON in configuration");
    }
  };

  return (
    <div className="space-y-4">
      <Input
        label="Step Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Select
        label="Step Type"
        options={stepTypes}
        value={type}
        onChange={(e) => setType(e.target.value)}
      />
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Configuration (JSON)
        </label>
        <textarea
          value={configJson}
          onChange={(e) => {
            setConfigJson(e.target.value);
            setError(null);
          }}
          rows={10}
          className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3.5 py-2.5 text-sm text-slate-100 font-mono placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
        />
        {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSave}>Save Configuration</Button>
      </div>
    </div>
  );
}
