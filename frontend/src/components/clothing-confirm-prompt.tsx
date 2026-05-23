"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ClothingItem, confirmWearable } from "@/lib/api";
import { toast } from "sonner";

interface ClothingConfirmPromptProps {
  item: ClothingItem;
  onResolved: (deleted: boolean) => void;
  compact?: boolean;
}

export function ClothingConfirmPrompt({
  item,
  onResolved,
  compact = false,
}: ClothingConfirmPromptProps) {
  const [loading, setLoading] = useState(false);

  const handleConfirm = async (confirmed: boolean) => {
    setLoading(true);
    try {
      const result = await confirmWearable(item.id, confirmed);
      if (result.deleted) {
        toast.success("Photo removed from wardrobe");
      } else {
        toast.success("Re-analyzing from photo…");
      }
      onResolved(result.deleted);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      className={`border-amber-500/30 bg-amber-500/10 ${compact ? "p-3" : "p-4"} space-y-3`}
    >
      <p className={`${compact ? "text-xs" : "text-sm"} text-amber-200/90 font-medium`}>
        Are you sure this is clothing or an outfit accessory?
      </p>
      {item.error_message && (
        <p className="text-[11px] text-slate-500 leading-relaxed">{item.error_message}</p>
      )}
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="outline"
          className="flex-1 border-slate-700 text-slate-300 hover:bg-slate-900"
          disabled={loading}
          onClick={() => handleConfirm(false)}
        >
          No, remove
        </Button>
        <Button
          size="sm"
          className="flex-1 bg-violet-600 hover:bg-violet-500 text-white"
          disabled={loading}
          onClick={() => handleConfirm(true)}
        >
          Yes, it&apos;s clothing
        </Button>
      </div>
    </Card>
  );
}
