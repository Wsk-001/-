"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Article } from "@/lib/types";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import Tabs from "@/components/ui/Tabs";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import Card, { CardContent } from "@/components/ui/Card";
import JsonTree from "@/components/viewer/JsonTree";
import HtmlPreview from "@/components/viewer/HtmlPreview";
import WechatFrame from "@/components/viewer/WechatFrame";

export default function ViewerPage() {
  const params = useParams();
  const router = useRouter();
  const articleId = params.articleId as string;

  const [article, setArticle] = useState<Article | null>(null);
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("json");

  const fetchArticle = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getArticle(articleId);
      setArticle(data);
      setError(null);

      try {
        const html = await api.getArticleHtml(articleId);
        setHtmlContent(html);
      } catch {
        setHtmlContent(data.html_content || "");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load article");
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => {
    fetchArticle();
  }, [fetchArticle]);

  const handleValidate = async () => {
    if (!article) return;
    try {
      const result = await api.validateArticle(article.id);
      setArticle((prev) => (prev ? { ...prev, validation: result } : null));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400 mb-4">{error || "Article not found"}</p>
        <Button variant="secondary" onClick={() => router.push("/dashboard")}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const tabs = [
    { id: "json", label: "JSON" },
    { id: "html", label: "HTML Preview" },
    { id: "wechat", label: "WeChat Preview" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h2 className="text-xl font-bold text-slate-100">{article.title}</h2>
            <p className="text-sm text-slate-400 mt-0.5">
              Created {formatDate(article.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {article.validation && (
            <Badge variant={article.validation.valid ? "success" : "error"}>
              {article.validation.valid ? "Valid" : "Invalid"}
            </Badge>
          )}
          <Button size="sm" variant="secondary" onClick={handleValidate}>
            Validate
          </Button>
        </div>
      </div>

      {article.validation && !article.validation.valid && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-red-400 text-sm font-medium mb-1">Validation Errors:</p>
          <ul className="list-disc list-inside text-red-400 text-xs space-y-0.5">
            {article.validation.errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
          {article.validation.warnings.length > 0 && (
            <>
              <p className="text-amber-400 text-sm font-medium mt-2 mb-1">Warnings:</p>
              <ul className="list-disc list-inside text-amber-400 text-xs space-y-0.5">
                {article.validation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <Card>
        <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
        <CardContent>
          {activeTab === "json" && (
            <div className="bg-slate-900 rounded-lg p-4 overflow-auto max-h-[600px] scrollbar-thin">
              <pre className="text-xs font-mono text-slate-300">
                <JsonTree data={article.content} />
              </pre>
            </div>
          )}
          {activeTab === "html" && <HtmlPreview html={htmlContent} />}
          {activeTab === "wechat" && <WechatFrame html={htmlContent} />}
        </CardContent>
      </Card>
    </div>
  );
}
