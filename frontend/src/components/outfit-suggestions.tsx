"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ClothingItem,
  getItem,
  OutfitPiece,
  OutfitSuggestion,
  OutfitSuggestResponse,
  suggestOutfits,
  getImageUrl,
} from "@/lib/api";
import { toast } from "sonner";

const OCCASIONS = [
  "casual",
  "formal",
  "business",
  "athletic",
  "evening",
  "weekend",
  "date-night",
  "outdoor",
];

const SEASONS = ["spring", "summer", "fall", "winter", "all-season"];

const STYLES = ["minimalist", "classic", "streetwear", "preppy", "sporty", "bohemian"];

function OutfitPieceCard({
  label,
  piece,
  onSelect,
}: {
  label: string;
  piece: OutfitPiece;
  onSelect: (itemId: number) => void;
}) {
  return (
    <button
      onClick={() => onSelect(piece.item_id)}
      className="flex items-center text-left w-full gap-2.5 p-2 rounded-lg bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors focus:outline-none"
    >
      <div className="w-12 h-12 rounded-md overflow-hidden bg-slate-900 flex-shrink-0">
        <img
          src={getImageUrl(piece.item_id)}
          alt={piece.clothing_type}
          className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{label}</p>
        <p className="text-xs text-slate-200 capitalize truncate">{piece.clothing_type}</p>
        {piece.colors && piece.colors.length > 0 && (
          <p className="text-[10px] text-slate-500 capitalize truncate">
            {piece.colors.join(", ")}
          </p>
        )}
      </div>
    </button>
  );
}

function OutfitCard({
  outfit,
  onSelectPiece,
}: {
  outfit: OutfitSuggestion;
  onSelectPiece: (itemId: number) => void;
}) {
  return (
    <Card className="p-4 border-slate-900 bg-slate-950 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">{outfit.name}</h3>
        <Badge className="bg-violet-600/10 text-violet-400 border border-violet-500/20 text-[10px]">
          AI Styled
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <OutfitPieceCard label="Top" piece={outfit.top} onSelect={onSelectPiece} />
        <OutfitPieceCard label="Bottom" piece={outfit.bottom} onSelect={onSelectPiece} />
        <OutfitPieceCard label="Footwear" piece={outfit.footwear} onSelect={onSelectPiece} />
        {outfit.outerwear && (
          <OutfitPieceCard label="Outerwear" piece={outfit.outerwear} onSelect={onSelectPiece} />
        )}
        {outfit.accessory && (
          <OutfitPieceCard label="Accessory" piece={outfit.accessory} onSelect={onSelectPiece} />
        )}
      </div>

      <p className="text-xs text-slate-400 leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-900/50">
        {outfit.reasoning}
      </p>
    </Card>
  );
}

function OutfitSkeleton() {
  return (
    <Card className="p-4 border-slate-900 bg-slate-950 space-y-3">
      <Skeleton className="h-5 w-1/3 bg-slate-900" />
      <div className="grid grid-cols-2 gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16 bg-slate-900 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-12 w-full bg-slate-900 rounded-lg" />
    </Card>
  );
}


export function OutfitSuggestions() {
  const [occasion, setOccasion] = useState("casual");
  const [season, setSeason] = useState("summer");
  const [style, setStyle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OutfitSuggestResponse | null>(null);

  // States for Zoom / Lightbox Modal
  const [activeItemId, setActiveItemId] = useState<number | null>(null);
  const [activeItem, setActiveItem] = useState<ClothingItem | null>(null);
  const [activeItemLoading, setActiveItemLoading] = useState(false);

  const handleSelectPiece = useCallback(async (itemId: number) => {
    setActiveItemId(itemId);
    setActiveItemLoading(true);
    setActiveItem(null);
    try {
      const data = await getItem(itemId);
      setActiveItem(data);
    } catch (err) {
      toast.error("Failed to load clothing item details");
    } finally {
      setActiveItemLoading(false);
    }
  }, []);

  const generate = useCallback(async () => {
    // If we already have a generated outfit, ask for confirmation
    if (result) {
      const confirmRegen = window.confirm("Are you sure you want to regenerate outfits?");
      if (!confirmRegen) return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await suggestOutfits({
        occasion,
        season,
        style: style || undefined,
      });
      setResult(data);
      toast.success(`Generated ${data.outfits.length} outfit suggestions`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate outfits";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [occasion, season, style, result]);

  return (
    <div className="p-4 md:p-6 animate-fade-in max-w-4xl md:mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-xl md:text-2xl font-bold text-slate-100">Outfit Picker</h1>
        <p className="text-xs md:text-sm text-slate-500 mt-1">
          AI stylist combinations from your wardrobe — color, occasion, and season aware.
        </p>
      </div>

      <Card className="p-4 border-slate-900 bg-slate-950 mb-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <Label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Occasion
            </Label>
            <select
              value={occasion}
              onChange={(e) => setOccasion(e.target.value)}
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              {OCCASIONS.map((o) => (
                <option key={o} value={o} className="capitalize">
                  {o}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Season
            </Label>
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              {SEASONS.map((s) => (
                <option key={s} value={s} className="capitalize">
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Style (optional)
            </Label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full h-9 px-3 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              <option value="">Any style</option>
              {STYLES.map((s) => (
                <option key={s} value={s} className="capitalize">
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button
          onClick={generate}
          disabled={loading}
          className="w-full sm:w-auto bg-violet-600 hover:bg-violet-500 text-white font-medium"
        >
          {loading ? "Styling your wardrobe..." : result ? "Regenerate Outfits" : "Generate Outfits"}
        </Button>
      </Card>

      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
          <p className="text-xs text-slate-500 mt-2">
            Upload and analyze at least 3 items (tops, bottoms, footwear) first.
          </p>
          <Link href="/upload" className="inline-block mt-3">
            <Button variant="outline" size="sm" className="border-slate-800 text-slate-300">
              Upload Items
            </Button>
          </Link>
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <OutfitSkeleton key={i} />
          ))}
        </div>
      )}

      {!loading && result && (
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            {result.outfits.length} outfits from {result.wardrobe_count} analyzed items
          </p>
          {result.outfits.map((outfit, i) => (
            <OutfitCard
              key={`${outfit.name}-${i}`}
              outfit={outfit}
              onSelectPiece={handleSelectPiece}
            />
          ))}
        </div>
      )}

      {!loading && !result && !error && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800/80 flex items-center justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-300 mb-1">Ready to style?</h3>
          <p className="text-slate-500 text-sm mb-6 max-w-sm">
            Pick an occasion and season, then let AI build complete outfits from your wardrobe.
          </p>
        </div>
      )}

      {/* Lightbox / Zoom Dialog Modal */}
      {activeItemId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-all duration-300">
          <div
            className="absolute inset-0 cursor-zoom-out"
            onClick={() => {
              setActiveItemId(null);
              setActiveItem(null);
            }}
          />
          <Card className="relative w-full max-w-lg overflow-hidden border-slate-800 bg-slate-900/95 shadow-2xl animate-in fade-in zoom-in duration-200 max-h-[90vh] flex flex-col">
            {/* Close button */}
            <button
              onClick={() => {
                setActiveItemId(null);
                setActiveItem(null);
              }}
              className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-slate-950/80 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>

            {activeItemLoading ? (
              <div className="p-12 space-y-4 flex flex-col items-center justify-center min-h-[300px]">
                <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm text-slate-400">Loading item details...</p>
              </div>
            ) : activeItem ? (
              <div className="overflow-y-auto flex-1 custom-scrollbar">
                <div className="relative aspect-square w-full bg-slate-950 flex items-center justify-center">
                  <img
                    src={getImageUrl(activeItem.id)}
                    alt={activeItem.clothing_type || activeItem.filename}
                    className="w-full h-full object-contain max-h-[50vh]"
                  />
                </div>
                <div className="p-5 space-y-4">
                  <div>
                    <h2 className="text-lg font-bold text-slate-100 capitalize">
                      {activeItem.user_label || activeItem.clothing_type || "Clothing Item"}
                    </h2>
                    {activeItem.clothing_type && activeItem.user_label && activeItem.user_label !== activeItem.clothing_type && (
                      <p className="text-xs text-slate-500 capitalize mt-0.5">
                        AI Category: {activeItem.clothing_type}
                      </p>
                    )}
                  </div>

                  {activeItem.description && (
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
                      {activeItem.description}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    {activeItem.material && (
                      <div>
                        <span className="font-semibold text-slate-400 block mb-1">Material</span>
                        <span className="text-slate-200 capitalize">{activeItem.material}</span>
                      </div>
                    )}
                    {activeItem.pattern && (
                      <div>
                        <span className="font-semibold text-slate-400 block mb-1">Pattern</span>
                        <span className="text-slate-200 capitalize">{activeItem.pattern}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2 pt-2 border-t border-slate-800">
                    <Link href={`/item/${activeItem.id}`} className="flex-1">
                      <Button className="w-full bg-violet-600 hover:bg-violet-500 text-white text-xs py-1.5 h-9">
                        View Full Details (Resets Outfits)
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setActiveItemId(null);
                        setActiveItem(null);
                      }}
                      className="border-slate-800 text-slate-300 hover:bg-slate-950 text-xs py-1.5 h-9"
                    >
                      Close Zoom
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400 min-h-[200px] flex items-center justify-center">
                Failed to load item details.
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

