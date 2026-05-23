"use client";

import { use } from "react";
import { Header } from "@/components/header";
import { ItemDetail } from "@/components/item-detail";

export default function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <>
      <Header />
      <main className="flex-1">
        <ItemDetail itemId={parseInt(id)} />
      </main>
    </>
  );
}
