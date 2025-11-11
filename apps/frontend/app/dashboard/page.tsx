import { RefreshButton } from "@/components/refresh-button";

import { DataTable } from "./data-table";
import { mockData } from "./mock-data";
import { columns } from "./columns";

export default function DashboardPage() {
  return (
    <div className="container mx-auto py-10">
      <div className="flex items-center justify-between mb-8 gap-4 flex-wrap">
        <h1 className="text-3xl font-bold">Live Surebet Opportunities</h1>
        <RefreshButton />
      </div>
      <DataTable columns={columns} data={mockData} />
    </div>
  );
}
