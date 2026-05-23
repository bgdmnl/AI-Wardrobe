"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ClothingItem, getItems } from "@/lib/api";
import { ClothingCard, ClothingCardSkeleton } from "@/components/clothing-card";
import { Button } from "@/components/ui/button";

export function Gallery() {
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    try {
      setError(null);
      const data = await getItems();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load items");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchItems();
    
    // Poll every 4 seconds for status updates of pending/processing items
    const interval = setInterval(() => {
      fetchItems();
    }, 4000);
    
    return () => clearInterval(interval);
  }, [fetchItems]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 p-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <ClothingCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center min-h-[50vh]">
        <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h3 className="text-md font-medium text-slate-300 mb-1">Failed to load wardrobe</h3>
        <p className="text-slate-500 text-sm mb-4 max-w-xs">{error}</p>
        <Button onClick={fetchItems} variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-900">
          Try Again
        </Button>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center min-h-[60vh]">
        <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800/80 flex items-center justify-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/>
          </svg>
        </div>
        <h3 className="text-lg font-medium text-slate-300 mb-1">Your wardrobe is empty</h3>
        <p className="text-slate-500 text-sm mb-6 max-w-xs">Upload your first clothing item to start tagging and organizing.</p>
        <Link href="/upload">
          <Button className="bg-violet-600 hover:bg-violet-500 text-white font-medium">
            Upload Clothing Item
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-md font-semibold text-slate-300">
          My Collection
          <span className="ml-1.5 text-xs font-normal text-slate-500">({items.length} items)</span>
        </h2>
        <Button onClick={fetchItems} variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
        </Button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 animate-fade-in">
        {items.map((item) => (
          <ClothingCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
