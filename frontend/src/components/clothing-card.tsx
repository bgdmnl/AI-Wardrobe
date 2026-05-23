"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ClothingItem, getImageUrl, getItemDisplayName } from "@/lib/api";

const statusConfig: Record<
  ClothingItem["status"],
  { label: string; className: string }
> = {
  pending: { label: "Pending", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
  processing: { label: "Analyzing...", className: "bg-blue-500/20 text-blue-400 border-blue-500/30 animate-pulse-soft" },
  completed: { label: "Ready", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  needs_confirmation: { label: "Review", className: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  error: { label: "Error", className: "bg-red-500/20 text-red-400 border-red-500/30" },
};

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

export function ClothingCard({ item }: { item: ClothingItem }) {
  const status = statusConfig[item.status];
  
  return (
    <Link href={`/item/${item.id}`}>
      <Card className="group overflow-hidden border-slate-900 bg-slate-950 hover:bg-slate-900/50 hover:border-slate-800 transition-all duration-300 cursor-pointer">
        <div className="relative aspect-square overflow-hidden bg-slate-900">
          <img
            src={getImageUrl(item.id)}
            alt={item.clothing_type || item.filename}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
          {item.status !== "completed" && (
            <div className="absolute inset-0 bg-slate-950/60 flex items-center justify-center">
              <Badge variant="outline" className={status.className}>
                {status.label}
              </Badge>
            </div>
          )}
        </div>
        <div className="p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm font-medium text-slate-200 truncate capitalize">
              {getItemDisplayName(item)}
            </span>
            {item.colors && item.colors.length > 0 && (
              <div className="flex gap-1 flex-shrink-0">
                {item.colors.slice(0, 3).map((color, i) => (
                  <div
                    key={i}
                    className={`w-3 h-3 rounded-full border ${colorMap[color.toLowerCase()] || "bg-slate-600 border-slate-700"}`}
                    title={color}
                  />
                ))}
              </div>
            )}
          </div>
          {item.tags && item.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 max-h-5 overflow-hidden">
              {item.tags.slice(0, 2).map((tag, i) => (
                <span key={i} className="text-xs text-slate-500">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </Card>
    </Link>
  );
}

export function ClothingCardSkeleton() {
  return (
    <Card className="overflow-hidden border-slate-900 bg-slate-950">
      <Skeleton className="aspect-square w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-2/3 bg-slate-900" />
        <Skeleton className="h-3 w-1/2 bg-slate-900" />
      </div>
    </Card>
  );
}
