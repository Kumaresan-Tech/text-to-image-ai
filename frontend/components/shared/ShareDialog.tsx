"use client";

import { useState, useEffect } from "react";
import { X, Link, Copy, Check, Eye, Trash2 } from "lucide-react";
import { imagesApi } from "@/lib/api";

interface ShareDialogProps {
  open: boolean;
  imageId: string;
  token: string;
  onClose: () => void;
}

interface ShareLink {
  id: string;
  share_token: string;
  share_url: string;
  is_active: boolean;
  view_count: number;
  created_at: string;
}

export function ShareDialog({ open, imageId, token, onClose }: ShareDialogProps) {
  const [shares, setShares] = useState<ShareLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    if (open) loadShares();
  }, [open, imageId]);

  async function loadShares() {
    setLoading(true);
    try {
      const data = await imagesApi.shares(imageId, token);
      setShares(data);
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function createShare() {
    try {
      const newShare = await imagesApi.share(imageId, token);
      setShares((prev) => [newShare, ...prev]);
    } catch {
    }
  }

  async function revokeShare(shareId: string) {
    try {
      await imagesApi.removeShare(shareId, token);
      setShares((prev) => prev.filter((s) => s.id !== shareId));
    } catch {
    }
  }

  async function copyLink(url: string, shareId: string) {
    await navigator.clipboard.writeText(url);
    setCopied(shareId);
    setTimeout(() => setCopied(null), 2000);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="glass rounded-xl w-full max-w-md p-5 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">Share Image</h3>
          <button onClick={onClose} className="h-7 w-7 rounded-md hover:bg-muted flex items-center justify-center">
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <button
          onClick={createShare}
          className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
        >
          <Link className="h-4 w-4" />
          Generate Share Link
        </button>

        <div className="space-y-2 max-h-60 overflow-y-auto">
          {loading && (
            <p className="text-xs text-muted-foreground text-center py-4">Loading shares...</p>
          )}

          {!loading && shares.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-4">No share links yet</p>
          )}

          {shares.map((share) => (
            <div key={share.id} className="bg-secondary/30 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2">
                <code className="text-[10px] text-muted-foreground truncate flex-1 font-mono">
                  {share.share_url}
                </code>
                <button
                  onClick={() => copyLink(share.share_url, share.id)}
                  className="h-7 w-7 rounded-md hover:bg-background flex items-center justify-center flex-shrink-0 transition-colors"
                >
                  {copied === share.id ? (
                    <Check className="h-3.5 w-3.5 text-green-500" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                </button>
                <button
                  onClick={() => revokeShare(share.id)}
                  className="h-7 w-7 rounded-md hover:bg-destructive/10 flex items-center justify-center flex-shrink-0 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </button>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                <span className="flex items-center gap-0.5">
                  <Eye className="h-2.5 w-2.5" /> {share.view_count} views
                </span>
                <span>{new Date(share.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
