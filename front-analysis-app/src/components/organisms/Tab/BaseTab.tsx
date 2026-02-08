import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "../../../lib/utils/helpers";

const Tabs = TabsPrimitive.Root;

const TabsList = ({ className, ...props }: TabsPrimitive.TabsListProps) => (
  <div className="mb-3 border-b border-brand-border">
    <TabsPrimitive.List
      className={cn("-mb-px flex space-x-8 overflow-x-auto", className)}
      {...props}
    />
  </div>
);

const TabsTrigger = ({ className, ...props }: TabsPrimitive.TabsTriggerProps) => (
  <TabsPrimitive.Trigger
    className={cn(
      "whitespace-nowrap py-4 px-1 border-b-2 text-sm transition-colors cursor-pointer focus:outline-none",
      // Inactive state matching sample.html
      "border-transparent text-text-main/60 font-medium hover:text-brand-border hover:border-brand-border",
      // Active state matching sample.html
      "data-[state=active]:border-brand-accent data-[state=active]:text-brand-accent data-[state=active]:font-bold",
      className
    )}
    {...props}
  />
);

const TabsContent = ({ className, ...props }: TabsPrimitive.TabsContentProps) => (
  <TabsPrimitive.Content
    className={cn("focus:outline-none", className)}
    {...props}
  />
);

export { Tabs, TabsContent, TabsList, TabsTrigger };
