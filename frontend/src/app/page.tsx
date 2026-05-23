import { Header } from "@/components/header";
import { Gallery } from "@/components/gallery";
import { AiModeBanner } from "@/components/ai-mode-banner";

export default function HomePage() {
  return (
    <>
      <Header />
      <AiModeBanner />
      <main className="flex-1">
        <Gallery />
      </main>
    </>
  );
}
