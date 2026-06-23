"use client";

import React from "react";
import { Prompt } from "@/lib/types";
import { Textarea } from "@/components/ui/Input";
import Input from "@/components/ui/Input";

interface PromptEditorProps {
  prompt: Prompt;
  onChange: (field: string, value: string) => void;
}

export default function PromptEditor({ prompt, onChange }: PromptEditorProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Prompt Name"
          value={prompt.name}
          onChange={(e) => onChange("name", e.target.value)}
          placeholder="Enter prompt name..."
        />
        <Input
          label="Category"
          value={prompt.category}
          onChange={(e) => onChange("category", e.target.value)}
          placeholder="e.g., writing, analysis, review..."
        />
      </div>
      <Textarea
        label="Prompt Content"
        value={prompt.content}
        onChange={(e) => onChange("content", e.target.value)}
        placeholder="Enter your prompt content here... Use {{variable_name}} for variables."
        rows={16}
        className="font-mono text-xs"
      />
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span>Version: {prompt.version}</span>
        <span>&middot;</span>
        <span>Variables: {prompt.variables.length}</span>
        <span>&middot;</span>
        <span>Use {"{{variable_name}}"} to inject variables</span>
      </div>
    </div>
  );
}
