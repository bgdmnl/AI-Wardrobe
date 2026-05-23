export interface ClothingItem {
  id: number;
  filename: string;
  filepath: string;
  status: "pending" | "processing" | "completed" | "error" | "needs_confirmation";
  user_label: string | null;
  clothing_type: string | null;
  colors: string[] | null;
  pattern: string | null;
  material: string | null;
  season: string[] | null;
  occasion: string[] | null;
  tags: string[] | null;
  description: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClothingItemList {
  items: ClothingItem[];
  total: number;
}

export interface HealthStatus {
  db: string;
  redis: string;
  ai: string;
  ai_provider: string;
}

export interface ClothingItemUpdate {
  user_label?: string | null;
  clothing_type?: string | null;
  tags?: string[];
}

export function getItemDisplayName(item: ClothingItem): string {
  if (item.status === "needs_confirmation") return "Needs review";
  return item.user_label || item.clothing_type || "Processing...";
}

export interface OutfitPiece {
  item_id: number;
  clothing_type: string;
  colors: string[] | null;
}

export interface OutfitSuggestion {
  name: string;
  top: OutfitPiece;
  bottom: OutfitPiece;
  footwear: OutfitPiece;
  outerwear: OutfitPiece | null;
  accessory: OutfitPiece | null;
  reasoning: string;
}

export interface OutfitSuggestResponse {
  outfits: OutfitSuggestion[];
  wardrobe_count: number;
}

export interface OutfitSuggestParams {
  occasion?: string;
  season?: string;
  style?: string;
}

export interface BatchUploadResult {
  message: string;
  items: ClothingItem[];
  uploaded: number;
  failed: number;
  errors: string[];
}

/** Human-readable label from filename (matches backend). */
export function labelFromFilename(filename: string): string {
  let stem = filename.replace(/^.*[/\\]/, "");
  const dot = stem.lastIndexOf(".");
  if (dot > 0) stem = stem.slice(0, dot);
  stem = stem.replace(/^(img|image|photo|pic|dsc|dscn|wp|screenshot)[-_]?\d*$/i, "");
  stem = stem.replace(/[-_]+/g, " ").replace(/\s+/g, " ").trim();
  if (!stem) return "";
  return stem.replace(/\b\w/g, (c) => c.toUpperCase());
}

export async function uploadImage(file: File): Promise<ClothingItem> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/items/upload", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  const data = await res.json();
  return data.item;
}

export async function uploadImagesBatch(files: File[]): Promise<BatchUploadResult> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const res = await fetch("/api/items/upload/batch", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json();
}

export async function getItems(skip = 0, limit = 50): Promise<ClothingItemList> {
  const res = await fetch(`/api/items?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.statusText}`);
  return res.json();
}

export async function getItem(id: number): Promise<ClothingItem> {
  const res = await fetch(`/api/items/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch item: ${res.statusText}`);
  return res.json();
}

export async function updateItem(
  id: number,
  data: ClothingItemUpdate
): Promise<ClothingItem> {
  const res = await fetch(`/api/items/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json();
}

export async function confirmWearable(
  id: number,
  confirmed: boolean
): Promise<{ message: string; item?: ClothingItem; deleted: boolean }> {
  const res = await fetch(`/api/items/${id}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json();
}

export async function reanalyzeItem(id: number): Promise<ClothingItem> {
  const res = await fetch(`/api/items/${id}/reanalyze`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? res.statusText);
  }
  const data = await res.json();
  return data.item;
}

export async function deleteItem(id: number): Promise<void> {
  const res = await fetch(`/api/items/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete item: ${res.statusText}`);
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export function getImageUrl(itemId: number): string {
  return `/api/items/${itemId}/image`;
}

export async function suggestOutfits(
  params: OutfitSuggestParams = {}
): Promise<OutfitSuggestResponse> {
  const res = await fetch("/api/outfits/suggest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      occasion: params.occasion ?? "casual",
      season: params.season ?? "summer",
      style: params.style ?? null,
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail ?? res.statusText;
    throw new Error(typeof detail === "string" ? detail : "Failed to generate outfits");
  }
  return res.json();
}
