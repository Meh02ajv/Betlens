"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse rounded bg-surface", className)}
      aria-hidden="true"
    />
  );
}

export function MatchCardSkeleton() {
  return (
    <div className="card flex items-center gap-3">
      <div className="flex-1 flex items-center gap-2">
        <Skeleton className="w-6 h-6 rounded-full" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="h-6 w-16" />
      <div className="flex-1 flex items-center justify-end gap-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="w-6 h-6 rounded-full" />
      </div>
    </div>
  );
}

export function StandingsSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 py-2">
          <Skeleton className="w-6 h-4" />
          <Skeleton className="w-6 h-6 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 w-8" />
        </div>
      ))}
    </div>
  );
}

export function PredictionSkeleton() {
  return (
    <div className="card space-y-4">
      <Skeleton className="h-5 w-32" />
      <Skeleton className="h-6 w-full rounded-full" />
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
      </div>
    </div>
  );
}