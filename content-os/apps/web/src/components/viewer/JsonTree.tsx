"use client";

import React, { useState } from "react";

interface JsonTreeProps {
  data: unknown;
  name?: string;
  level?: number;
}

export default function JsonTree({ data, name, level = 0 }: JsonTreeProps) {
  const [collapsed, setCollapsed] = useState(level > 2);

  if (data === null) {
    return (
      <span className="text-slate-500">
        {name && <span className="text-blue-400">{name}</span>}
        {name && ": "}
        null
      </span>
    );
  }

  if (typeof data === "boolean") {
    return (
      <span>
        {name && <span className="text-blue-400">{name}</span>}
        {name && ": "}
        <span className="text-amber-400">{data.toString()}</span>
      </span>
    );
  }

  if (typeof data === "number") {
    return (
      <span>
        {name && <span className="text-blue-400">{name}</span>}
        {name && ": "}
        <span className="text-emerald-400">{data}</span>
      </span>
    );
  }

  if (typeof data === "string") {
    return (
      <span>
        {name && <span className="text-blue-400">{name}</span>}
        {name && ": "}
        <span className="text-amber-300">&quot;{data}&quot;</span>
      </span>
    );
  }

  if (Array.isArray(data)) {
    if (collapsed) {
      return (
        <span
          className="cursor-pointer text-slate-400 hover:text-slate-200"
          onClick={() => setCollapsed(false)}
        >
          {name && <span className="text-blue-400">{name}</span>}
          {name && ": "}
          [{data.length} items]
        </span>
      );
    }
    return (
      <div style={{ paddingLeft: level > 0 ? "1rem" : "0" }}>
        <span
          className="cursor-pointer text-slate-400 hover:text-slate-200"
          onClick={() => setCollapsed(true)}
        >
          {name && <span className="text-blue-400">{name}</span>}
          {name && ": "}
          [
        </span>
        {data.map((item, i) => (
          <div key={i} style={{ paddingLeft: "1rem" }}>
            <JsonTree data={item} level={level + 1} />
            {i < data.length - 1 && <span className="text-slate-500">,</span>}
          </div>
        ))}
        <span>]</span>
      </div>
    );
  }

  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (collapsed) {
      return (
        <span
          className="cursor-pointer text-slate-400 hover:text-slate-200"
          onClick={() => setCollapsed(false)}
        >
          {name && <span className="text-blue-400">{name}</span>}
          {name && ": "}
          {"{"}...{entries.length} keys{"}"}
        </span>
      );
    }
    return (
      <div style={{ paddingLeft: level > 0 ? "1rem" : "0" }}>
        <span
          className="cursor-pointer text-slate-400 hover:text-slate-200"
          onClick={() => setCollapsed(true)}
        >
          {name && <span className="text-blue-400">{name}</span>}
          {name && ": "}
          {"{"}
        </span>
        {entries.map(([key, value], i) => (
          <div key={key} style={{ paddingLeft: "1rem" }}>
            <JsonTree data={value} name={key} level={level + 1} />
            {i < entries.length - 1 && <span className="text-slate-500">,</span>}
          </div>
        ))}
        <span>{"}"}</span>
      </div>
    );
  }

  return <span>{String(data)}</span>;
}
