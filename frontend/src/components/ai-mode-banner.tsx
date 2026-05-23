"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

export function AiModeBanner() {
  const [provider, setProvider] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => setProvider(h.ai_provider))
      .catch(() => setProvider(null));
  }, []);

  if (provider !== "mock") return null;

  return (
    <div className="mx-4 mt-3 md:mx-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-200/90 text-xs leading-relaxed">
      <strong className="text-amber-300">Mock AI is on</strong> — uploads get random wrong labels
      because no vision model is connected. Open each item, set the correct{" "}
      <strong>name</strong>, save, then <strong>Re-analyze</strong>, or set up Ollama
      (guide: <code className="text-amber-100/80">test/OLLAMA_SETUP.md</code>).
    </div>
  );
}
