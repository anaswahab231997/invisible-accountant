import { useState, useEffect } from 'react';

interface QueueItem {
  id: number;
  intake_id: number;
  timestamp: string;
  vendor: string;
  amount: number;
  category: string;
  is_ambiguous: boolean;
  auditor_question: string | null;
  status: string;
}

export default function Dashboard() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
      const response = await fetch('/api/queue?limit=50');
      const data = await response.json();
      setQueue(data.queue || []);
    } catch (e) {
      console.error("Failed to fetch queue", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();

    const handleWsUpdate = (e: Event) => {
      const { detail } = e as CustomEvent;
      if (detail.type === 'INTAKE_UPDATE') {
        // Refresh queue when an update happens
        fetchQueue();
      }
    };

    window.addEventListener('ws-update', handleWsUpdate);
    return () => window.removeEventListener('ws-update', handleWsUpdate);
  }, []);

  return (
    <div className="w-full max-w-4xl bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Expense Queue</h2>
      
      {loading ? (
        <div className="text-gray-500">Loading expenses...</div>
      ) : queue.length === 0 ? (
        <div className="text-gray-500">No expenses in the queue yet.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3">Timestamp</th>
                <th scope="col" className="px-6 py-3">Vendor</th>
                <th scope="col" className="px-6 py-3">Category</th>
                <th scope="col" className="px-6 py-3">Amount</th>
                <th scope="col" className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {queue.map(item => (
                <tr key={item.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">{new Date(item.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{item.vendor}</td>
                  <td className="px-6 py-4">{item.category}</td>
                  <td className="px-6 py-4">£{item.amount.toFixed(2)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${item.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                      {item.status}
                    </span>
                    {item.is_ambiguous && <p className="text-xs text-red-500 mt-1">Ambiguous</p>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
