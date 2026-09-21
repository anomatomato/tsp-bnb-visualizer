import { Button } from "./ui/button"

export const TestComponent = () => {
  return (
    <div className="@container flex w-sm flex-col gap-2 p-8 text-sm font-medium selection:bg-fuchsia-300 sm:items-center sm:max-xl:gap-6">
      <button
        data-active
        popoverTarget="my-popover"
        className="border bg-primary text-primary-foreground data-active:border-purple-500"
      >
        Check for updates
      </button>
      <div
        popover="auto"
        id="my-popover"
        className="underline decoration-sky-500/30 opacity-0 transition-opacity duration-300 open:opacity-100 starting:open:opacity-0"
      >
        Updates
      </div>
      <input
        type="email"
        className="peer/mail rounded-md border border-gray-300 px-3 py-2 placeholder:text-gray-500 placeholder:italic invalid:border-pink-500 invalid:text-pink-500"
        placeholder="Email"
      />
      <ul className="text-black *:rounded-full *:border *:border-sky-100 *:bg-sky-50 *:px-2">
        <li>Sales</li>
        <li>Marketing</li>
      </ul>

      <p className="invisible -inset-1 -skew-y-2 peer-invalid/mail:visible peer-invalid/mail:text-pink-500">
        Please provide a valid email
      </p>
      <input
        type="file"
        className="file:mr-4 file:rounded-full file:border-0 file:bg-violet-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-violet-700 hover:file:bg-violet-100"
      />
      <button className="rounded-lg bg-[#316ff6] px-3 py-1 ring-1 blur-sm grayscale hover:bg-sky-600 dark:bg-sky-800! dark:hover:bg-sky-600">
        Save changes
      </button>
      <Button variant="outline">Save changes</Button>
      <div className="@container">
        <div className="flex flex-col @md:flex-row">hello world</div>
      </div>
    </div>
  )
}
