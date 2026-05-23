import { Header } from "@/components/header";
import { OutfitSuggestions } from "@/components/outfit-suggestions";

export default function OutfitsPage() {
  return (
    <>
      <Header />
      <main className="flex-1">
        <OutfitSuggestions />
      </main>
    </>
  );
}
