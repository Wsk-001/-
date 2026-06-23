"use client";

import React from "react";
import Input from "@/components/ui/Input";
import Card, { CardContent } from "@/components/ui/Card";

interface VarInjectorProps {
  variables: string[];
  values: Record<string, string>;
  onValueChange: (variable: string, value: string) => void;
}

export default function VarInjector({
  variables,
  values,
  onValueChange,
}: VarInjectorProps) {
  if (variables.length === 0) {
    return (
      <Card>
        <CardContent>
          <p className="text-sm text-slate-500 text-center py-4">
            No variables detected. Use {"{{variable_name}}"} in the prompt content.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-slate-300">
        Variable Injection ({variables.length} variables)
      </p>
      <div className="space-y-2">
        {variables.map((variable) => (
          <div key={variable} className="flex items-center gap-3">
            <span className="text-xs font-mono text-blue-400 w-32 shrink-0 truncate">
              {"{{"}{variable}{"}}"}
            </span>
            <Input
              placeholder={`Enter value for ${variable}...`}
              value={values[variable] || ""}
              onChange={(e) => onValueChange(variable, e.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
