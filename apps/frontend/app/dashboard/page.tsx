import { DataTable } from "./data-table";
import { mockData } from "./mock-data";
import { columns } from "./columns";

export default function DashboardPage() {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-8">Live Surebet Opportunities</h1>
      <DataTable columns={columns} data={mockData} />
    </div>
  );
}
