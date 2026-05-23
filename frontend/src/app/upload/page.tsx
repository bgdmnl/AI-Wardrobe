import { Header } from "@/components/header";
import { UploadForm } from "@/components/upload-form";

export default function UploadPage() {
  return (
    <>
      <Header />
      <main className="flex-1">
        <UploadForm />
      </main>
    </>
  );
}
