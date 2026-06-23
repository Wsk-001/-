"use client";

import React, { useState, useEffect, useCallback } from "react";
import { LLMConfig, Template } from "@/lib/types";
import { api } from "@/lib/api";
import Card, { CardContent, CardHeader } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Spinner from "@/components/ui/Spinner";

export default function SettingsPage() {
  const [llmConfigs, setLlmConfigs] = useState<LLMConfig[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAddLlm, setShowAddLlm] = useState(false);
  const [newLlmName, setNewLlmName] = useState("");
  const [newLlmProvider, setNewLlmProvider] = useState("openai");
  const [newLlmModel, setNewLlmModel] = useState("gpt-4");
  const [newLlmApiKey, setNewLlmApiKey] = useState("");
  const [newLlmTemperature, setNewLlmTemperature] = useState("0.7");
  const [newLlmMaxTokens, setNewLlmMaxTokens] = useState("4096");
  const [creating, setCreating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [configs, tmpls] = await Promise.all([
        api.getLlmConfigs(),
        api.getTemplates(),
      ]);
      setLlmConfigs(configs);
      setTemplates(tmpls);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateLlm = async () => {
    if (!newLlmName || !newLlmModel) return;
    try {
      setCreating(true);
      const config = await api.createLlmConfig({
        name: newLlmName,
        provider: newLlmProvider,
        model: newLlmModel,
        temperature: parseFloat(newLlmTemperature),
        max_tokens: parseInt(newLlmMaxTokens),
      } as Partial<LLMConfig>);
      setLlmConfigs((prev) => [...prev, config]);
      setShowAddLlm(false);
      setNewLlmName("");
      setNewLlmProvider("openai");
      setNewLlmModel("gpt-4");
      setNewLlmApiKey("");
      setNewLlmTemperature("0.7");
      setNewLlmMaxTokens("4096");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create LLM config");
    } finally {
      setCreating(false);
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
    <div className="max-w-4xl mx-auto space-y-8">
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* LLM Configs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-100">LLM Configurations</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Manage your language model providers and settings
              </p>
            </div>
            <Button size="sm" onClick={() => setShowAddLlm(true)}>
              + Add Config
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {llmConfigs.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-6">
              No LLM configurations yet. Add one to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {llmConfigs.map((config) => (
                <div
                  key={config.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-slate-900 border border-slate-700"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        {config.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {config.provider} / {config.model}
                      </p>
                    </div>
                    <Badge variant={config.api_key_set ? "success" : "warning"}>
                      {config.api_key_set ? "API Key Set" : "No API Key"}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>Temp: {config.temperature}</span>
                    <span>Max Tokens: {config.max_tokens}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Templates */}
      <Card>
        <CardHeader>
          <div>
            <h3 className="text-base font-semibold text-slate-100">HTML Templates</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Available article templates for content formatting
            </p>
          </div>
        </CardHeader>
        <CardContent>
          {templates.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-6">
              No templates available.
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="p-4 rounded-lg bg-slate-900 border border-slate-700"
                >
                  <p className="text-sm font-medium text-slate-200">
                    {template.name}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {template.description || "No description"}
                  </p>
                  <p className="text-xs text-slate-600 mt-2 font-mono truncate">
                    {template.file_path}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* WeChat Config (Placeholder) */}
      <Card>
        <CardHeader>
          <div>
            <h3 className="text-base font-semibold text-slate-100">WeChat Configuration</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              WeChat Official Account API settings
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-sm text-slate-500 mb-2">
              WeChat integration is not yet configured
            </p>
            <p className="text-xs text-slate-600">
              Configure your WeChat Official Account credentials to enable publishing
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Add LLM Config Modal */}
      <Modal
        isOpen={showAddLlm}
        onClose={() => setShowAddLlm(false)}
        title="Add LLM Configuration"
      >
        <div className="space-y-4">
          <Input
            label="Config Name"
            placeholder="e.g., GPT-4 Production"
            value={newLlmName}
            onChange={(e) => setNewLlmName(e.target.value)}
          />
          <Select
            label="Provider"
            options={[
              { value: "openai", label: "OpenAI" },
              { value: "anthropic", label: "Anthropic" },
              { value: "azure", label: "Azure OpenAI" },
              { value: "local", label: "Local / Custom" },
            ]}
            value={newLlmProvider}
            onChange={(e) => setNewLlmProvider(e.target.value)}
          />
          <Input
            label="Model"
            placeholder="e.g., gpt-4, claude-3-opus"
            value={newLlmModel}
            onChange={(e) => setNewLlmModel(e.target.value)}
          />
          <Input
            label="API Key"
            type="password"
            placeholder="sk-..."
            value={newLlmApiKey}
            onChange={(e) => setNewLlmApiKey(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              value={newLlmTemperature}
              onChange={(e) => setNewLlmTemperature(e.target.value)}
            />
            <Input
              label="Max Tokens"
              type="number"
              value={newLlmMaxTokens}
              onChange={(e) => setNewLlmMaxTokens(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowAddLlm(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateLlm}
              disabled={!newLlmName || !newLlmModel || creating}
            >
              {creating ? "Creating..." : "Add Configuration"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
