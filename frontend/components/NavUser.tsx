"use client";

import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function NavUser() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <div className="w-6 h-6 rounded-full bg-gray-700 animate-pulse" />;
  }

  if (!session) {
    return (
      <div className="flex items-center gap-3">
        <Link href="/auth/login">
          <Button variant="ghost" size="sm">Sign in</Button>
        </Link>
        <Link href="/auth/signup">
          <Button size="sm">Sign up</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-300">
        {session.user?.name ?? session.user?.email}
      </span>
      <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: "/auth/login" })}>
        Sign out
      </Button>
    </div>
  );
}
