"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface RefreshButtonProps {
  onClick?: () => void | Promise<void>;
}

export function RefreshButton({ onClick }: RefreshButtonProps) {
  const router = useRouter();
  const [isPending, startTransition] = React.useTransition();

  const handleClick = () => {
    if (onClick) {
      startTransition(async () => {
        await onClick();
      });
    } else {
      startTransition(() => {
        router.refresh();
      });
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleClick}
      disabled={isPending}
    >
      <RefreshCcw className={cn("h-4 w-4", isPending && "animate-spin")} />
      <span className="ml-2 hidden sm:inline">Refresh</span>
    </Button>
  );
}
