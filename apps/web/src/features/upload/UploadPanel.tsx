import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { uploadArchive } from "@/shared/api/jobs";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";

const steps = [
  "queued",
  "unpacking",
  "preprocessing",
  "layout",
  "geometry",
  "ocr",
  "assembling",
  "exporting",
  "packaging",
  "completed",
];

export function UploadPanel(props: { onJobStarted: (id: string) => void }) {
  const [profile, setProfile] = useState("balanced");
  const [busy, setBusy] = useState(false);

  const onDrop = useCallback(
    async (files: File[]) => {
      const f = files[0];
      if (!f) return;
      setBusy(true);
      try {
        const res = await uploadArchive(f, profile);
        toast.success("Job queued");
        props.onJobStarted(res.job_id);
      } catch (e) {
        toast.error((e as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [profile, props]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: { "application/zip": [".zip"], "application/x-7z-compressed": [".7z"] },
  });

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-lg font-semibold">Upload archive</h2>
        <p className="mt-2 text-sm text-slate-600">
          Supported: ZIP with JPG/PNG/TIFF inside. RAR/7z supported in backend containers with tools installed.
        </p>
        <div className="mt-4 flex gap-3">
          <label className="text-sm text-slate-700">Profile</label>
          <select
            className="rounded-md border border-border px-2 py-1 text-sm"
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
          >
            <option value="balanced">balanced</option>
            <option value="quality">quality</option>
            <option value="low_vram">low_vram</option>
          </select>
        </div>
        <div
          {...getRootProps()}
          className={`mt-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 transition ${
            isDragActive ? "border-accent bg-muted" : "border-border"
          }`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="h-10 w-10 text-accent" />
          <p className="mt-3 text-sm text-slate-600">Drag & drop or click to select</p>
          <Button className="mt-4" disabled={busy} type="button">
            {busy ? "Uploading…" : "Choose file"}
          </Button>
        </div>
      </Card>
      <Card>
        <h3 className="font-medium">Pipeline stages</h3>
        <ul className="mt-3 grid grid-cols-2 gap-2 text-sm text-slate-600 md:grid-cols-3">
          {steps.map((s) => (
            <li key={s} className="rounded-md bg-muted px-2 py-1">
              {s}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
