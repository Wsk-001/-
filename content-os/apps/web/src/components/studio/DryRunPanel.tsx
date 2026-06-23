"use client";

import React from "react";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Card, { CardContent } from "@/components/ui/Card";

interface DryRunPanelProps {
  result: { output: string; tokens_used: number } | null;
  loading: boolean;
  onRun: () => void;
}

export default function DryRunPanel({ result, loading, onRun }: DryRunPanelProps) {
  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-slate-300">Dry Run</p>
          <Button size="sm" onClick={onRun} disabled={loading}>
            {loading ? (
              <span className="flex items-center gap-2">
                <Spinner size="sm" />
                Running...
              </span>
            ) : (
              "Run Test"
            )}
          </Button>
        </div>
        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Tokens used: {result.tokens_used}</span>
            </div>
            <div className="bg-slate-900 rounded-lg p-4 max-h-64 overflow-y-auto scrollbar-thin">
              <pre className="text-xs text-slate-300 whitespace-pre-wrap">
                {result.output}
              </pre>
            </div>
          </div>
        )}
        {!result && !loading && (
          <p className="text-xs text-slate-500 text-center py-4">
            Fill in the variables and click Run Test to see the output.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
