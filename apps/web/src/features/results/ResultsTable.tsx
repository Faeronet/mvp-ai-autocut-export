import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { listJobs, downloadUrl } from "@/shared/api/jobs";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";

export function ResultsTable() {
  const q = useQuery({ queryKey: ["jobs"], queryFn: listJobs, refetchInterval: 5000 });
  return (
    <Card>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Completed jobs</h2>
        <Button variant="ghost" onClick={() => q.refetch()}>
          Refresh
        </Button>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-slate-500">
              <th className="py-2">Job</th>
              <th>Status</th>
              <th>Pages</th>
              <th>Updated</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {q.data?.map((j) => (
              <tr key={j.id} className="border-b border-border/60">
                <td className="py-2 font-mono text-xs">{j.id}</td>
                <td>{j.status}</td>
                <td>
                  {j.completed_pages}/{j.total_pages}
                </td>
                <td className="text-xs text-slate-500">{new Date(j.updated_at).toLocaleString()}</td>
                <td className="text-right">
                  {j.result_archive_path && (
                    <a href={downloadUrl(j.id)}>
                      <Button type="button" variant="primary">
                        <Download className="mr-2 h-4 w-4" />
                        ZIP
                      </Button>
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {q.isLoading && <div className="py-6 text-center text-sm text-slate-500">Loading…</div>}
        {!q.isLoading && (!q.data || q.data.length === 0) && (
          <div className="py-10 text-center text-sm text-slate-500">No jobs yet</div>
        )}
      </div>
    </Card>
  );
}
