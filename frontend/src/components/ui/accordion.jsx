import * as React from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = React.forwardRef(
  ({ className, ...props }, ref) => (
    <AccordionPrimitive.Item
      ref={ref}
      className={cn(
        "rounded-sm overflow-hidden border-3 border-brutal-black dark:border-[#43474D] shadow-brutal mb-4 bg-white dark:bg-[#242629]",
        className
      )}
      {...props}
    />
  )
);
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef(
  ({ className, children, ...props }, ref) => (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        ref={ref}
        className={cn(
          "flex flex-1 items-center justify-between text-brutal-black dark:text-white bg-white dark:bg-[#242629] p-4 md:p-6 font-bold font-mono text-left transition-all hover:bg-brutal-yellow/20 dark:hover:bg-[#2C2F33] [&[data-state=open]>svg]:rotate-180 [&[data-state=open]]:bg-brutal-yellow/30 dark:[&[data-state=open]]:bg-[#2C2F33] [&[data-state=open]]:border-b-3 [&[data-state=open]]:border-brutal-black dark:[&[data-state=open]]:border-[#43474D]",
          className
        )}
        {...props}
      >
        {children}
        <ChevronDown className="h-5 w-5 md:h-6 md:w-6 shrink-0 transition-transform duration-300 text-brutal-black dark:text-white" />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  )
);
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = React.forwardRef(
  ({ className, children, ...props }, ref) => (
    <AccordionPrimitive.Content
      ref={ref}
      className="overflow-hidden bg-white dark:bg-[#1E2124] text-brutal-black/80 dark:text-[#B9BBBE] text-sm md:text-base transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
      {...props}
    >
      <div className={cn("p-4 md:p-6", className)}>{children}</div>
    </AccordionPrimitive.Content>
  )
);

AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
