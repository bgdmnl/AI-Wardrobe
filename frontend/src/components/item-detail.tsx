"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ClothingItem,
  getItem,
  deleteItem,
  getImageUrl,
  getItemDisplayName,
  updateItem,
  reanalyzeItem,
} from "@/lib/api";
import { Label } from "@/components/ui/label";
import { ClothingConfirmPrompt } from "@/components/clothing-confirm-prompt";
import { toast } from "sonner";

const colorMap: Record<string, string> = {
  black: "bg-gray-950 border-slate-800",
  white: "bg-white border-slate-300",
  navy: "bg-blue-900 border-blue-950",
  gray: "bg-gray-500 border-gray-600",
  red: "bg-red-500 border-red-600",
  blue: "bg-blue-500 border-blue-600",
  green: "bg-green-600 border-green-700",
  beige: "bg-amber-100 border-amber-200",
  brown: "bg-amber-800 border-amber-900",
  pink: "bg-pink-400 border-pink-500",
  olive: "bg-lime-800 border-lime-900",
  burgundy: "bg-red-950 border-red-950",
  cream: "bg-amber-50 border-amber-100",
  teal: "bg-teal-500 border-teal-600",
  coral: "bg-orange-400 border-orange-500",
};

export function ItemDetail({ itemId }: { itemId: number }) {
  const [item, setItem] = useState<ClothingItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("");
  const [editTags, setEditTags] = useState("");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchItem = useCallback(async () => {
    try {
      const data = await getItem(itemId);
      setItem(data);
      setEditName(data.user_label ?? "");
      setEditType(data.clothing_type ?? "");
      setEditTags((data.tags ?? []).join(", "));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load item details");
    } finally {
      setLoading(false);
    }
  }, [itemId]);

  useEffect(() => {
    fetchItem();
  }, [fetchItem]);

  // If item is not completed or error, poll to check when it finishes
  useEffect(() => {
    if (
      !item ||
      item.status === "completed" ||
      item.status === "error" ||
      item.status === "needs_confirmation"
    )
      return;

    const interval = setInterval(() => {
      fetchItem();
    }, 3000);

    return () => clearInterval(interval);
  }, [item, fetchItem]);

  const parseTags = (raw: string) =>
    raw
      .split(/[,#]+/)
      .map((t) => t.trim())
      .filter(Boolean);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateItem(itemId, {
        user_label: editName.trim() || null,
        clothing_type: editType.trim() || null,
        tags: parseTags(editTags),
      });
      setItem(updated);
      toast.success("Saved name and tags");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleReanalyze = async () => {
    if (!editName.trim() && !editType.trim() && !parseTags(editTags).length) {
      toast.error("Set an item name or tags first");
      return;
    }
    setReanalyzing(true);
    try {
      const saved = await updateItem(itemId, {
        user_label: editName.trim() || null,
        clothing_type: editType.trim() || null,
        tags: parseTags(editTags),
      });
      setItem(saved);
      const queued = await reanalyzeItem(itemId);
      setItem(queued);
      toast.success("Re-analysis started — page will update automatically");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Re-analyze failed");
    } finally {
      setReanalyzing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this clothing item?")) return;
    setDeleting(true);
    try {
      await deleteItem(itemId);
      toast.success("Clothing item deleted");
      router.push("/");
    } catch (err) {
      toast.error("Failed to delete item");
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 space-y-4 animate-pulse-soft">
        <div className="relative aspect-[3/4] w-full rounded-xl overflow-hidden bg-slate-900">
          <Skeleton className="w-full h-full bg-slate-900" />
        </div>
        <Skeleton className="h-6 w-1/3 bg-slate-900" />
        <Skeleton className="h-4 w-full bg-slate-900" />
        <Skeleton className="h-4 w-3/4 bg-slate-900" />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="p-8 text-center min-h-[50vh] flex flex-col items-center justify-center">
        <p className="text-slate-400 mb-4">{error || "Clothing item not found"}</p>
        <Button onClick={() => router.push("/")} variant="outline" className="border-slate-800 hover:bg-slate-900">
          Back to Gallery
        </Button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in pb-8 md:pb-12">
      <div className="md:grid md:grid-cols-2 md:gap-8 md:p-6 md:max-w-6xl md:mx-auto">
      {/* Image Container */}
      <div className="relative aspect-[3/4] w-full bg-slate-950 border-b border-slate-900 md:border md:rounded-xl md:overflow-hidden md:aspect-[4/5] md:sticky md:top-20 md:self-start">
        <img
          src={getImageUrl(item.id)}
          alt={item.clothing_type || item.filename}
          className="w-full h-full object-cover"
        />
        <button
          onClick={() => router.push("/")}
          className="absolute top-4 left-4 w-9 h-9 rounded-full bg-slate-950/80 border border-slate-900 flex items-center justify-center text-slate-300 hover:text-white transition-colors"
          title="Back to gallery"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
        </button>
      </div>

      {/* Item metadata content */}
      <div className="p-4 space-y-4 md:p-0 md:pt-2">
        {item.status === "needs_confirmation" && (
          <ClothingConfirmPrompt
            item={item}
            onResolved={(deleted) => {
              if (deleted) {
                router.push("/");
                return;
              }
              fetchItem();
            }}
          />
        )}

        {/* Status notification */}
        {item.status !== "completed" && item.status !== "needs_confirmation" && (
          <Card className={`p-3 border-slate-900 ${item.status === "error" ? "bg-red-500/5" : "bg-blue-500/5"}`}>
            <div className="flex items-start gap-3">
              {item.status === "error" ? (
                <>
                  <div className="w-7 h-7 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-red-400">Analysis Failed</p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-normal">{item.error_message || "A pipeline error occurred while analyzing the image."}</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0 animate-pulse-soft">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="12" y1="2" x2="12" y2="6"/>
                      <line x1="12" y1="18" x2="12" y2="22"/>
                      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                      <line x1="2" y1="12" x2="6" y2="12"/>
                      <line x1="18" y1="12" x2="22" y2="12"/>
                      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
                      <line x1="16.24" y1="9.64" x2="19.07" y2="6.81"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-blue-400">Analyzing Clothing...</p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-normal">Running local vision/text models. This page will update automatically.</p>
                  </div>
                </>
              )}
            </div>
          </Card>
        )}

        {/* Heading */}
        <div>
          <h1 className="text-xl font-bold text-slate-100 capitalize">
            {getItemDisplayName(item)}
          </h1>
          {item.clothing_type && item.user_label && item.user_label !== item.clothing_type && (
            <p className="text-xs text-slate-500 capitalize mt-0.5">
              AI category: {item.clothing_type}
            </p>
          )}
          {item.material && (
            <p className="text-xs text-slate-400 capitalize mt-1 font-medium">
              {item.material} {item.pattern && item.pattern !== "solid" && `• ${item.pattern}`}
            </p>
          )}
        </div>

        {/* Edit name & tags */}
        <Card className="p-4 border-slate-900 bg-slate-950/80 space-y-3">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Correct name & tags
          </h3>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Names are set by AI from the photo. Use this only to correct a wrong name, then
            Re-analyze. Filenames are hints only — not used as the display name.
          </p>
          <div className="space-y-1.5">
            <Label className="text-[10px] text-slate-500">Item name</Label>
            <input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="e.g. Dark blue baggy jeans"
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[10px] text-slate-500">Category (optional)</Label>
            <input
              value={editType}
              onChange={(e) => setEditType(e.target.value)}
              placeholder="e.g. jeans, sneakers, t-shirt"
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[10px] text-slate-500">Tags (comma-separated)</Label>
            <input
              value={editTags}
              onChange={(e) => setEditTags(e.target.value)}
              placeholder="jeans, baggy, light blue"
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-2 pt-1">
            <Button
              variant="outline"
              className="flex-1 border-slate-800 text-slate-300 hover:bg-slate-900"
              onClick={handleSave}
              disabled={saving || reanalyzing}
            >
              {saving ? "Saving..." : "Save"}
            </Button>
            <Button
              className="flex-1 bg-violet-600 hover:bg-violet-500 text-white"
              onClick={handleReanalyze}
              disabled={saving || reanalyzing || item.status === "processing"}
            >
              {reanalyzing ? "Re-analyzing..." : "Save & Re-analyze"}
            </Button>
          </div>
        </Card>

        {/* AI Description */}
        {item.description && (
          <p className="text-slate-300 text-sm leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-900/50">
            {item.description}
          </p>
        )}

        <Separator className="bg-slate-900" />

        {/* Colors Section */}
        {item.colors && item.colors.length > 0 && (
          <div>
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Detected Colors</h3>
            <div className="flex flex-wrap gap-2">
              {item.colors.map((color, i) => (
                <div key={i} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950 border border-slate-900">
                  <div className={`w-3 h-3 rounded-full border ${colorMap[color.toLowerCase()] || "bg-slate-600 border-slate-700"}`} />
                  <span className="text-xs text-slate-300 capitalize">{color}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Season & Occasion Grid */}
        <div className="grid grid-cols-2 gap-4">
          {item.season && item.season.length > 0 && (
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Season</h3>
              <div className="flex flex-wrap gap-1.5">
                {item.season.map((s, i) => (
                  <Badge key={i} variant="outline" className="border-slate-800 text-slate-400 bg-slate-950/20 capitalize font-normal text-[11px] px-2 py-0.5">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {item.occasion && item.occasion.length > 0 && (
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Occasion</h3>
              <div className="flex flex-wrap gap-1.5">
                {item.occasion.map((o, i) => (
                  <Badge key={i} variant="outline" className="border-slate-800 text-slate-400 bg-slate-950/20 capitalize font-normal text-[11px] px-2 py-0.5">
                    {o}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tags Section */}
        {item.tags && item.tags.length > 0 && (
          <div>
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Tags</h3>
            <div className="flex flex-wrap gap-1.5">
              {item.tags.map((tag, i) => (
                <Badge key={i} className="bg-violet-600/10 text-violet-400 border border-violet-500/20 hover:bg-violet-600/20 font-medium text-[11px] px-2.5 py-0.5">
                  #{tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <Separator className="bg-slate-900" />

        {/* Delete Item */}
        <div className="pt-2">
          <Button
            variant="ghost"
            className="w-full text-red-500 hover:text-red-400 hover:bg-red-500/5 text-sm"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? "Deleting..." : "Delete clothing item"}
          </Button>
        </div>
      </div>
      </div>
    </div>
  );
}
