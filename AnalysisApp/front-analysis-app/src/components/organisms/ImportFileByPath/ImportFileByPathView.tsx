import type { TableInfosType } from "../../../types/stateTypes";

type TablePanelProps = {
  tableInfos: TableInfosType;
};

export function TablePanel({ tableInfos }: TablePanelProps) {

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex flex-col gap-8">
        <header>
          <h1 className="text-3xl font-bold text-black dark:text-white">Select a File</h1>
          <p className="mt-2 text-base text-black/60 dark:text-white/60">Choose a file to begin your regression analysis
            or data shaping.</p>
        </header>
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-grow">
              <span
                className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-black/40 dark:text-white/40">search</span>
              <input
                className="w-full rounded-lg border-primary/20 bg-transparent py-2 pl-10 pr-4 text-black dark:text-white placeholder:text-black/40 dark:placeholder:text-white/40 focus:border-primary focus:ring-primary/50"
                placeholder="Search files by name" type="text" />
            </div>
            <div className="flex items-center gap-2">
              <button
                className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors">
                <span className="material-symbols-outlined text-xl">arrow_upward</span>
              </button>
              <nav className="flex items-center gap-2 text-sm font-medium text-black/60 dark:text-white/60">
                <a className="hover:text-primary dark:hover:text-primary" href="#">Projects</a>
                <span className="material-symbols-outlined text-base">chevron_right</span>
                <a className="hover:text-primary dark:hover:text-primary" href="#">Analysis Q4</a>
              </nav>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full bg-primary/10 dark:bg-primary/20 px-4 text-sm font-medium text-primary hover:bg-primary/20 dark:hover:bg-primary/30">
              <span>All Files</span>
              <span className="material-symbols-outlined text-base">expand_more</span>
            </button>
            <button
              className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full bg-transparent px-4 text-sm font-medium text-black/60 dark:text-white/60 hover:bg-primary/10 dark:hover:bg-primary/20 hover:text-primary dark:hover:text-primary">
              <span>CSV Files</span>
            </button>
            <button
              className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full bg-transparent px-4 text-sm font-medium text-black/60 dark:text-white/60 hover:bg-primary/10 dark:hover:bg-primary/20 hover:text-primary dark:hover:text-primary">
              <span>Excel Files</span>
            </button>
          </div>
        </div>
        <div className="overflow-hidden rounded-xl border border-primary/20">
          <table className="w-full">
            <thead className="bg-primary/5 dark:bg-primary/10">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                  File Name</th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                  Size</th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                  Last Modified</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-primary/20 bg-background-light dark:bg-background-dark">
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-primary">folder</span><span>Reports</span></div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">-</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-15 11:00 AM
                </td>
              </tr>
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-black/40 dark:text-white/40">description</span><span>data_2023.csv</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2.5 MB</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-15 10:30 AM
                </td>
              </tr>
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-black/40 dark:text-white/40">description</span><span>sales_report.xlsx</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">1.8 MB</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-14 03:45 PM
                </td>
              </tr>
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-black/40 dark:text-white/40">description</span><span>customer_data.csv</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">3.2 MB</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-13 09:15 AM
                </td>
              </tr>
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-black/40 dark:text-white/40">description</span><span>product_catalog.xlsx</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2.1 MB</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-12 01:20 PM
                </td>
              </tr>
              <tr className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2"><span
                      className="material-symbols-outlined text-black/40 dark:text-white/40">description</span><span>inventory_data.csv</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">1.5 MB</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">2023-11-11 05:50 PM
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="flex justify-end gap-3">
          <button
            className="flex min-w-[120px] max-w-xs cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary/20 dark:bg-primary/30 text-black dark:text-white text-sm font-bold hover:bg-primary/30 dark:hover:bg-primary/40 transition-colors">
            <span className="truncate">Cancel</span>
          </button>
          <button
            className="flex min-w-[120px] max-w-xs cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold hover:bg-primary/80 transition-colors">
            <span className="truncate">Select File</span>
          </button>
        </div>
      </div>
    </div>
  );
}
